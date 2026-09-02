"""Chunk → embed → upsert pipeline for Qdrant."""

from __future__ import annotations

import os
import uuid
from dataclasses import dataclass, field
from typing import Any

from src.memory.embeddings.provider import EmbeddingConfig, EmbeddingProvider, build_embedding_provider
from src.memory.qdrant_store import QdrantMemoryStore, RetrievedChunk
from src.memory.chunking import DocumentChunk, chunk_document


@dataclass(slots=True)
class EmbeddingPipelineConfig:
    qdrant_url: str = "http://localhost:6333"
    collection: str = "neometis_workspace"
    embedding: EmbeddingConfig = field(default_factory=EmbeddingConfig)
    child_chunk_size: int = 512


@dataclass(slots=True)
class IndexResult:
    doc_id: str
    chunks_indexed: int
    collection: str


class EmbeddingPipeline:
    """Embed document chunks and store them in Qdrant."""

    def __init__(self, config: EmbeddingPipelineConfig | None = None) -> None:
        cfg = config or EmbeddingPipelineConfig(
            qdrant_url=os.environ.get("QDRANT_URL", "http://localhost:6333"),
            collection=os.environ.get("QDRANT_COLLECTION", "neometis_workspace"),
        )
        self.config = cfg
        self.embedder: EmbeddingProvider = build_embedding_provider(cfg.embedding)
        self.store = QdrantMemoryStore(
            url=cfg.qdrant_url,
            collection=cfg.collection,
            vector_size=self.embedder.dimensions,
        )

    async def ensure_ready(self) -> None:
        await self.store.ensure_collection()

    async def close(self) -> None:
        await self.store.close()

    async def embed_query(self, query: str) -> list[float]:
        return await self.embedder.embed_one(query)

    async def index_text(
        self,
        doc_id: str,
        text: str,
        metadata: dict[str, Any] | None = None,
    ) -> IndexResult:
        """Chunk a document, embed each chunk, and upsert into Qdrant."""
        chunks = chunk_document(text, doc_id, child_size=self.config.child_chunk_size)
        # Index child chunks only — parents are metadata anchors for future Parent-Child RAG.
        indexable = [c for c in chunks if c.metadata.get("role") == "child"]
        if not indexable:
            indexable = chunks

        await self._upsert_chunks(indexable, metadata or {})
        return IndexResult(
            doc_id=doc_id,
            chunks_indexed=len(indexable),
            collection=self.config.collection,
        )

    async def index_chunks(
        self,
        chunks: list[DocumentChunk],
        metadata: dict[str, Any] | None = None,
    ) -> IndexResult:
        await self._upsert_chunks(chunks, metadata or {})
        doc_id = chunks[0].id.split("::")[0] if chunks else "unknown"
        return IndexResult(doc_id=doc_id, chunks_indexed=len(chunks), collection=self.config.collection)

    async def search(self, query: str, top_k: int = 5) -> list[RetrievedChunk]:
        vector = await self.embed_query(query)
        return await self.store.search(vector, top_k=top_k)

    async def _upsert_chunks(
        self,
        chunks: list[DocumentChunk],
        metadata: dict[str, Any],
    ) -> None:
        if not chunks:
            return

        batch_size = self.config.embedding.batch_size
        for start in range(0, len(chunks), batch_size):
            batch = chunks[start : start + batch_size]
            vectors = await self.embedder.embed([c.text for c in batch])
            points = []
            for chunk, vector in zip(batch, vectors, strict=True):
                point_id = str(uuid.uuid5(uuid.NAMESPACE_URL, chunk.id))
                payload = {
                    "text": chunk.text,
                    "chunk_id": chunk.id,
                    "parent_id": chunk.parent_id,
                    **chunk.metadata,
                    **metadata,
                }
                points.append((point_id, vector, payload))
            await self.store.upsert_points(points)
