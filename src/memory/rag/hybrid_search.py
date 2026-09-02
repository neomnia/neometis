"""Hybrid BM25 + dense vector search over Qdrant."""

from __future__ import annotations

from dataclasses import dataclass

from src.memory.qdrant_store import QdrantMemoryStore, RetrievedChunk


@dataclass(slots=True)
class HybridSearchConfig:
    dense_weight: float = 0.7
    sparse_weight: float = 0.3
    top_k: int = 20


class HybridSearcher:
    """Combines dense Qdrant search with sparse BM25 (sparse vectors TBD)."""

    def __init__(self, store: QdrantMemoryStore, config: HybridSearchConfig | None = None) -> None:
        self.store = store
        self.config = config or HybridSearchConfig()

    async def search(
        self,
        query_vector: list[float],
        query_text: str = "",
    ) -> list[RetrievedChunk]:
        # Dense leg is wired; BM25 sparse leg lands in a follow-up PR.
        _ = query_text
        return await self.store.search(query_vector, top_k=self.config.top_k)
