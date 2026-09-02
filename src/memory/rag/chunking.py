"""Parent-Child semantic chunking for workspace documents."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class DocumentChunk:
    id: str
    text: str
    parent_id: str | None
    metadata: dict[str, Any]


def chunk_document(text: str, doc_id: str, child_size: int = 512) -> list[DocumentChunk]:
    """Split a document into a parent summary and child chunks (stub)."""
    parent = DocumentChunk(
        id=f"{doc_id}::parent",
        text=text[: child_size * 2],
        parent_id=None,
        metadata={"role": "parent"},
    )
    children = [
        DocumentChunk(
            id=f"{doc_id}::child::{idx}",
            text=text[i : i + child_size],
            parent_id=parent.id,
            metadata={"role": "child", "offset": i},
        )
        for idx, i in enumerate(range(0, len(text), child_size))
    ]
    return [parent, *children]
