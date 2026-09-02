"""Advanced RAG orchestrator — substitutes Hermes MemoryManager for NéoMêtis."""

from __future__ import annotations

import os
from dataclasses import dataclass

from src.memory.qdrant_store import QdrantMemoryStore, RetrievedChunk
from src.memory.rag.chunking import chunk_document
from src.memory.rag.hybrid_search import HybridSearcher
from src.memory.rag.reranker import Reranker


@dataclass(slots=True)
class RAGConfig:
    qdrant_url: str = "http://localhost:6333"
    collection: str = "neometis_workspace"
    vector_size: int = 1536
    rerank_model: str = "bge-reranker-base"


class AdvancedRAGPipeline:
    """Hybrid search + reranking pipeline backed by Qdrant."""

    def __init__(self, config: RAGConfig | None = None) -> None:
        cfg = config or RAGConfig(
            qdrant_url=os.environ.get("QDRANT_URL", "http://localhost:6333"),
            collection=os.environ.get("QDRANT_COLLECTION", "neometis_workspace"),
        )
        self.config = cfg
        self.store = QdrantMemoryStore(
            url=cfg.qdrant_url,
            collection=cfg.collection,
            vector_size=cfg.vector_size,
        )
        self.searcher = HybridSearcher(self.store)
        self.reranker = Reranker(model=cfg.rerank_model)

    async def ensure_ready(self) -> None:
        await self.store.ensure_collection()

    async def retrieve(
        self,
        query: str,
        query_vector: list[float],
        top_k: int = 5,
    ) -> list[RetrievedChunk]:
        candidates = await self.searcher.search(query_vector, query_text=query)
        return self.reranker.rerank(query, candidates, top_k=top_k)

    def index_document(self, doc_id: str, text: str) -> int:
        """Return chunk count (embedding upsert TBD)."""
        chunks = chunk_document(text, doc_id)
        return len(chunks)
