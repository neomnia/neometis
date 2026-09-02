"""
Qdrant-backed memory store for NéoMêtis's Advanced RAG pipeline.

Implements the storage/retrieval boundary used by the Hermes agent:
hybrid search (BM25 + dense vectors), Parent-Child semantic chunking,
and a reranking hook (BGE / FlashRank). This module defines the
interface and a thin Qdrant client wrapper; the actual embedding and
reranking models are pluggable.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models as qmodels


@dataclass(slots=True)
class RetrievedChunk:
    """A single retrieved document chunk with its relevance score."""

    id: str
    text: str
    score: float
    metadata: dict[str, Any]


class QdrantMemoryStore:
    """Thin async wrapper around Qdrant for the Advanced RAG pipeline."""

    def __init__(
        self,
        url: str = "http://localhost:6333",
        collection: str = "neometis_workspace",
        vector_size: int = 1536,
    ) -> None:
        self.collection = collection
        self.vector_size = vector_size
        self._client = AsyncQdrantClient(url=url)

    async def ensure_collection(self) -> None:
        """Create the target collection if it does not already exist."""
        collections = await self._client.get_collections()
        existing = {c.name for c in collections.collections}
        if self.collection in existing:
            return

        await self._client.create_collection(
            collection_name=self.collection,
            vectors_config=qmodels.VectorParams(
                size=self.vector_size,
                distance=qmodels.Distance.COSINE,
            ),
        )

    async def search(
        self,
        query_vector: list[float],
        top_k: int = 5,
    ) -> list[RetrievedChunk]:
        """Dense-vector search over the collection (hybrid/rerank TBD)."""
        results = await self._client.search(
            collection_name=self.collection,
            query_vector=query_vector,
            limit=top_k,
        )
        return [
            RetrievedChunk(
                id=str(point.id),
                text=(point.payload or {}).get("text", ""),
                score=point.score,
                metadata=point.payload or {},
            )
            for point in results
        ]

    async def close(self) -> None:
        await self._client.close()
