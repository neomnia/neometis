"""Advanced RAG orchestrator — substitutes Hermes MemoryManager for NéoMêtis."""

from __future__ import annotations

import os
from dataclasses import dataclass

from src.memory.embeddings import EmbeddingPipeline, EmbeddingPipelineConfig
from src.memory.qdrant_store import RetrievedChunk
from src.memory.rag.hybrid_search import HybridSearcher
from src.memory.rag.reranker import Reranker


@dataclass(slots=True)
class RAGConfig:
    qdrant_url: str = "http://localhost:6333"
    collection: str = "neometis_workspace"
    vector_size: int = 1536
    rerank_model: str = "bge-reranker-base"


class AdvancedRAGPipeline:
    """Embedding + retrieval pipeline backed by Qdrant."""

    def __init__(self, config: RAGConfig | None = None) -> None:
        cfg = config or RAGConfig(
            qdrant_url=os.environ.get("QDRANT_URL", "http://localhost:6333"),
            collection=os.environ.get("QDRANT_COLLECTION", "neometis_workspace"),
        )
        self.config = cfg
        self.embeddings = EmbeddingPipeline(
            EmbeddingPipelineConfig(qdrant_url=cfg.qdrant_url, collection=cfg.collection)
        )
        self.searcher = HybridSearcher(self.embeddings.store)
        self.reranker = Reranker(model=cfg.rerank_model)

    @property
    def store(self):
        return self.embeddings.store

    async def ensure_ready(self) -> None:
        await self.embeddings.ensure_ready()

    async def close(self) -> None:
        await self.embeddings.close()

    async def embed_query(self, query: str) -> list[float]:
        return await self.embeddings.embed_query(query)

    async def index_document(
        self,
        doc_id: str,
        text: str,
        metadata: dict | None = None,
    ) -> int:
        result = await self.embeddings.index_text(doc_id, text, metadata)
        return result.chunks_indexed

    async def retrieve(self, query: str, top_k: int = 5) -> list[RetrievedChunk]:
        query_vector = await self.embed_query(query)
        candidates = await self.searcher.search(query_vector, query_text=query)
        return self.reranker.rerank(query, candidates, top_k=top_k)
