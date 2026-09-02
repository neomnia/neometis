"""BGE / FlashRank reranking stage."""

from __future__ import annotations

from src.memory.qdrant_store import RetrievedChunk


class Reranker:
    """Rerank retrieved chunks with BGE or FlashRank (stub — pass-through for now)."""

    def __init__(self, model: str = "bge-reranker-base") -> None:
        self.model = model

    def rerank(self, query: str, chunks: list[RetrievedChunk], top_k: int = 5) -> list[RetrievedChunk]:
        _ = query
        return sorted(chunks, key=lambda c: c.score, reverse=True)[:top_k]
