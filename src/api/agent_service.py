"""Shared Hermes agent and RAG pipeline for API + Chainlit."""

from __future__ import annotations

import asyncio
import logging
import os
from collections.abc import AsyncGenerator

from src.core.hermes import HermesAgent, upstream_available
from src.core.hermes.events import AgentEvent, EventType
from src.memory.qdrant_config import qdrant_collection, qdrant_url
from src.memory.rag import AdvancedRAGPipeline, RAGConfig
from src.memory.rag.doc_indexer import run_background_rescan, run_startup_indexer
from src.tools import build_penpot_tools, build_plane_tools, build_specs_tools

logger = logging.getLogger(__name__)

_rag: AdvancedRAGPipeline | None = None
_rescan_task: asyncio.Task | None = None

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
    global _rag, _rescan_task
    _rag = AdvancedRAGPipeline(
        RAGConfig(qdrant_url=qdrant_url(), collection=qdrant_collection())
    )
    try:
        await _rag.ensure_ready()
        stats = await run_startup_indexer(_rag)
        if stats["files_indexed"]:
            logger.info("Workspace docs indexed: %s", stats)
        interval = int(os.environ.get("NEOMETIS_DOC_RESCAN_SECONDS", "60"))
        _rescan_task = asyncio.create_task(run_background_rescan(_rag, interval))
    except Exception as exc:  # noqa: BLE001
        logger.warning("RAG init failed: %s", exc)
        _rag = None


async def close_rag() -> None:
    global _rag, _rescan_task
    if _rescan_task is not None:
        _rescan_task.cancel()
        _rescan_task = None
    if _rag is not None:
        await _rag.store.close()
        _rag = None


async def index_uploaded_text(filename: str, text: str) -> int:
    if _rag is None:
        raise RuntimeError("RAG pipeline unavailable")
    return await _rag.index_document(f"upload::{filename}", text, {"source": "chainlit_upload"})


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
    "index_uploaded_text",
    "init_rag",
    "stream_agent_events",
    "upstream_available",
]
