"""Resolve Qdrant connection settings from environment."""

from __future__ import annotations

import os


def qdrant_url() -> str:
    explicit = os.environ.get("QDRANT_URL", "").strip()
    if explicit:
        return explicit

    host = os.environ.get("RAG_QDRANT_HOST", "localhost").strip()
    port = os.environ.get("RAG_QDRANT_PORT", "6333").strip()
    scheme = os.environ.get("RAG_QDRANT_SCHEME", "http").strip()
    return f"{scheme}://{host}:{port}"


def qdrant_collection() -> str:
    return os.environ.get("QDRANT_COLLECTION", "neometis_workspace")
