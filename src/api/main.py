"""
NéoMêtis API
=============

FastAPI entrypoint exposing the Hermes agent over a Server-Sent Events (SSE)
streaming endpoint, plus a lightweight health check for orchestration
(docker-compose / Kubernetes readiness probes).
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from src.core.agent import HermesAgent

app = FastAPI(
    title="NéoMêtis API",
    description="The Lean, Single-Tenant AI Workbench powered by Hermes Agent & Advanced RAG.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

agent = HermesAgent()


class ChatRequest(BaseModel):
    """Payload for a chat/agent invocation."""

    message: str
    session_id: str | None = None


@app.get("/health")
async def health() -> dict[str, str]:
    """Liveness/readiness probe used by docker-compose and load balancers."""
    return {"status": "ok", "service": "neometis-core"}


async def _stream_agent_response(message: str) -> AsyncGenerator[str, None]:
    async for event in agent.run(message):
        yield event.to_sse()


@app.post("/api/chat/stream")
async def chat_stream(request: ChatRequest) -> StreamingResponse:
    """Stream the Hermes agent's reasoning and tool calls as SSE events."""
    return StreamingResponse(
        _stream_agent_response(request.message),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("src.api.main:app", host="0.0.0.0", port=8000, reload=True)
