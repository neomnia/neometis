"""Shared Hermes agent and RAG pipeline for API + Chainlit."""

from __future__ import annotations

import os
from collections.abc import AsyncGenerator

from src.core.hermes import HermesAgent, upstream_available
from src.core.hermes.events import AgentEvent, EventType
from src.memory.qdrant_config import qdrant_collection, qdrant_url
from src.memory.rag import AdvancedRAGPipeline, RAGConfig
from src.tools import build_penpot_tools, build_plane_tools, build_specs_tools

_rag: AdvancedRAGPipeline | None = None

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


async def init_rag() -> None:
    global _rag
    _rag = AdvancedRAGPipeline(
        RAGConfig(qdrant_url=qdrant_url(), collection=qdrant_collection())
    )
    try:
        await _rag.ensure_ready()
    except Exception:
        _rag = None


async def close_rag() -> None:
    global _rag
    if _rag is not None:
        await _rag.store.close()
        _rag = None


def get_rag() -> AdvancedRAGPipeline | None:
    return _rag


async def stream_agent_events(message: str, use_rag: bool = False) -> AsyncGenerator[AgentEvent, None]:
    if use_rag and _rag is not None:
        chunks = await _rag.retrieve(message, top_k=3)
        if chunks:
            context = "\n\n".join(c.text for c in chunks if c.text)
            message = f"Context:\n{context}\n\nUser: {message}"

    async for event in agent.run(message):
        yield event


__all__ = [
    "AgentEvent",
    "EventType",
    "agent",
    "close_rag",
    "get_rag",
    "init_rag",
    "stream_agent_events",
    "upstream_available",
]
