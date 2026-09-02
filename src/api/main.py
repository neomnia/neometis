"""
NéoMêtis API + Chainlit workbench
===================================

FastAPI engine (SSE, RAG, health) with Chainlit UI mounted at ``/``.
Local: http://localhost:8000 — Remote: Traefik TLS + optional Basic Auth.
"""

from __future__ import annotations

import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from src.api.agent_service import (
    agent,
    close_rag,
    get_rag,
    init_rag,
    stream_agent_events,
    upstream_available,
)
from src.neometis.version import __version__


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_rag()
    yield
    await close_rag()


app = FastAPI(
    title="NéoMêtis",
    description="The Lean, Single-Tenant AI Workbench — Chainlit UI + Hermes Agent + Advanced RAG.",
    version=__version__,
    lifespan=lifespan,
)

_cors_origins = os.environ.get("CORS_ORIGINS", "http://localhost:3000,http://localhost:8000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _cors_origins if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    session_id: str | None = None
    use_rag: bool = False


class IndexDocumentRequest(BaseModel):
    doc_id: str = Field(..., min_length=1)
    text: str = Field(..., min_length=1)
    metadata: dict[str, str] = Field(default_factory=dict)


@app.get("/health")
async def health() -> dict[str, str]:
    from src.core.hermes.upstream import vendored_metadata

    meta = vendored_metadata()
    rag = get_rag()
    return {
        "status": "ok",
        "service": "neometis-app",
        "version": __version__,
        "hermes_engine": agent.engine_mode,
        "hermes_upstream_available": str(upstream_available()).lower(),
        "hermes_vendored_ref": meta.get("ref", ""),
        "rag_enabled": str(rag is not None).lower(),
        "embedding_provider": os.environ.get("EMBEDDING_PROVIDER", "openai"),
        "ui": "chainlit",
    }


async def _stream_agent_response(message: str, use_rag: bool) -> AsyncGenerator[str, None]:
    async for event in stream_agent_events(message, use_rag=use_rag):
        yield event.to_sse()


@app.post("/api/rag/index")
async def rag_index(request: IndexDocumentRequest) -> dict[str, str | int]:
    rag = get_rag()
    if rag is None:
        return {"status": "error", "message": "RAG pipeline unavailable (is Qdrant running?)"}

    count = await rag.index_document(request.doc_id, request.text, request.metadata)
    return {
        "status": "ok",
        "doc_id": request.doc_id,
        "chunks_indexed": count,
        "collection": rag.config.collection,
    }


@app.post("/api/chat/stream")
async def chat_stream(request: ChatRequest) -> StreamingResponse:
    """SSE endpoint for external clients (Next.js, scripts, integrations)."""
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


# Chainlit UI at / — register API routes above before mounting.
from chainlit.utils import mount_chainlit

mount_chainlit(app=app, target="src/ui/chainlit_app.py", path="/")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("src.api.main:app", host="0.0.0.0", port=8000, reload=True)
