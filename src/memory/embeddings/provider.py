"""Embedding providers for the Qdrant indexing pipeline."""

from __future__ import annotations

import hashlib
import math
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass

import httpx


@dataclass(slots=True)
class EmbeddingConfig:
    """Configuration for text embedding."""

    model: str = "text-embedding-3-small"
    api_base_url: str = "https://api.openai.com/v1"
    api_key: str = ""
    dimensions: int = 1536
    batch_size: int = 32
    provider: str = "openai"  # openai | hash (local dev fallback)


class EmbeddingProvider(ABC):
    """Embed text into dense vectors."""

    @property
    @abstractmethod
    def dimensions(self) -> int: ...

    @abstractmethod
    async def embed(self, texts: list[str]) -> list[list[float]]: ...

    async def embed_one(self, text: str) -> list[float]:
        vectors = await self.embed([text])
        return vectors[0]


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """OpenAI-compatible ``/v1/embeddings`` provider (OpenAI, Ollama, vLLM, etc.)."""

    def __init__(self, config: EmbeddingConfig) -> None:
        self._config = config
        if not config.api_key:
            raise ValueError("EMBEDDING_API_KEY is required for the openai embedding provider")

    @property
    def dimensions(self) -> int:
        return self._config.dimensions

    async def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        url = f"{self._config.api_base_url.rstrip('/')}/embeddings"
        headers = {
            "Authorization": f"Bearer {self._config.api_key}",
            "Content-Type": "application/json",
        }
        payload: dict = {"model": self._config.model, "input": texts}
        if self._config.dimensions:
            payload["dimensions"] = self._config.dimensions

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

        items = sorted(data["data"], key=lambda item: item["index"])
        return [item["embedding"] for item in items]


class HashEmbeddingProvider(EmbeddingProvider):
    """Deterministic local embedder for dev/tests without an external API."""

    def __init__(self, dimensions: int = 1536) -> None:
        self._dimensions = dimensions

    @property
    def dimensions(self) -> int:
        return self._dimensions

    async def embed(self, texts: list[str]) -> list[list[float]]:
        return [_hash_to_vector(text, self._dimensions) for text in texts]


def _hash_to_vector(text: str, dimensions: int) -> list[float]:
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    values: list[float] = []
    seed = int.from_bytes(digest[:8], "big")
    while len(values) < dimensions:
        seed = (seed * 1_103_515_245 + 12_345) & 0xFFFFFFFFFFFFFFFF
        values.append((seed / 0xFFFFFFFFFFFFFFFF) * 2 - 1)
    norm = math.sqrt(sum(v * v for v in values)) or 1.0
    return [v / norm for v in values]


def build_embedding_provider(config: EmbeddingConfig | None = None) -> EmbeddingProvider:
    """Factory — prefers OpenAI-compatible API, falls back to hash embedder in dev."""
    cfg = config or EmbeddingConfig(
        model=os.environ.get("EMBEDDING_MODEL", "text-embedding-3-small"),
        api_base_url=os.environ.get("EMBEDDING_API_BASE_URL", "https://api.openai.com/v1"),
        api_key=os.environ.get("EMBEDDING_API_KEY", ""),
        dimensions=int(os.environ.get("EMBEDDING_DIMENSIONS", "1536")),
        batch_size=int(os.environ.get("EMBEDDING_BATCH_SIZE", "32")),
        provider=os.environ.get("EMBEDDING_PROVIDER", "openai").lower(),
    )

    if cfg.provider == "hash":
        return HashEmbeddingProvider(dimensions=cfg.dimensions)

    if cfg.api_key:
        return OpenAIEmbeddingProvider(cfg)

    # Dev fallback when no API key is configured.
    return HashEmbeddingProvider(dimensions=cfg.dimensions)
