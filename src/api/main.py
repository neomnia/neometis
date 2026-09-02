"""
NéoMêtis API
=============

FastAPI entrypoint that wraps the Hermes engine (upstream or lean fallback)
behind Server-Sent Events (SSE) so any external UI — notably the Next.js 15
frontend — can consume reasoning tokens and tool calls in real time.
"""

from __future__ import annotations

import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from src.core.hermes import HermesAgent, upstream_available
from src.memory.rag import AdvancedRAGPipeline, RAGConfig
from src.neometis.version import __version__
from src.tools import build_penpot_tools, build_plane_tools, build_specs_tools

_rag: AdvancedRAGPipeline | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _rag
    _rag = AdvancedRAGPipeline(RAGConfig())
    try:
        await _rag.ensure_ready()
    except Exception:
        # Qdrant may be unavailable during local dev without Docker.
        _rag = None
    yield
    if _rag is not None:
        await _rag.store.close()


app = FastAPI(
    title="NéoMêtis API",
    description="The Lean, Single-Tenant AI Workbench powered by Hermes Agent & Advanced RAG.",
    version=__version__,
    lifespan=lifespan,
)

_cors_origins = os.environ.get("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _cors_origins if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_native_tools = [
    *build_specs_tools(),
    *build_penpot_tools(),
    *build_plane_tools(),
]

agent = HermesAgent(
    tools=_native_tools,
    model=os.environ.get("HERMES_MODEL_NAME"),
    base_url=os.environ.get("HERMES_API_BASE_URL"),
    api_key=os.environ.get("HERMES_API_KEY"),
)


class ChatRequest(BaseModel):
    """Payload for a chat/agent invocation."""

    message: str = Field(..., min_length=1)
    session_id: str | None = None
    use_rag: bool = False


@app.get("/health")
async def health() -> dict[str, str]:
    """Liveness/readiness probe used by docker-compose and load balancers."""
    from src.core.hermes.upstream import vendored_metadata

    meta = vendored_metadata()
    return {
        "status": "ok",
        "service": "neometis-core",
        "version": __version__,
        "hermes_engine": agent.engine_mode,
        "hermes_upstream_available": str(upstream_available()).lower(),
        "hermes_vendored_ref": meta.get("ref", ""),
        "rag_enabled": str(_rag is not None).lower(),
    }


async def _stream_agent_response(message: str, use_rag: bool) -> AsyncGenerator[str, None]:
    # RAG prefetch hook — inject retrieved context before the Hermes loop runs.
    if use_rag and _rag is not None:
        # Embedding generation is pluggable; vector stub keeps the API contract stable.
        stub_vector = [0.0] * _rag.config.vector_size
        chunks = await _rag.retrieve(message, stub_vector, top_k=3)
        if chunks:
            context = "\n\n".join(c.text for c in chunks if c.text)
            message = f"Context:\n{context}\n\nUser: {message}"

    async for event in agent.run(message):
        yield event.to_sse()


@app.post("/api/chat/stream")
async def chat_stream(request: ChatRequest) -> StreamingResponse:
    """Stream Hermes reasoning and tool calls as SSE events."""
    return StreamingResponse(
        _stream_agent_response(request.message, request.use_rag),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "X-Neometis-Version": __version__,
            "X-Hermes-Engine": agent.engine_mode,
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("src.api.main:app", host="0.0.0.0", port=8000, reload=True)
