"""Auto-index documents from workspace/docs into Qdrant."""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Any

from src.memory.rag.document_loader import SUPPORTED_EXTENSIONS, extract_text

logger = logging.getLogger(__name__)


def docs_directory() -> Path:
    raw = os.environ.get("NEOMETIS_DOCS_DIR", "./workspace/docs")
    return Path(raw).expanduser().resolve()


def manifest_path() -> Path:
    state_dir = Path(os.environ.get("NEOMETIS_STATE_DIR", "./workspace/.neometis"))
    return state_dir.resolve() / "indexed_docs.json"


def _file_signature(path: Path) -> str:
    stat = path.stat()
    digest = hashlib.sha256()
    digest.update(str(stat.st_mtime_ns).encode())
    digest.update(str(stat.st_size).encode())
    digest.update(path.name.encode())
    return digest.hexdigest()


class WorkspaceDocIndexer:
    """Scan workspace/docs and index new or changed files."""

    def __init__(self, rag_pipeline: Any) -> None:
        self._rag = rag_pipeline
        self._manifest: dict[str, str] = {}
        self._load_manifest()

    def _load_manifest(self) -> None:
        path = manifest_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.is_file():
            try:
                self._manifest = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                self._manifest = {}

    def _save_manifest(self) -> None:
        manifest_path().write_text(json.dumps(self._manifest, indent=2), encoding="utf-8")

    def discover_files(self) -> list[Path]:
        root = docs_directory()
        root.mkdir(parents=True, exist_ok=True)
        return sorted(
            p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS
        )

    async def index_file(self, path: Path) -> int:
        rel = str(path.relative_to(docs_directory()))
        signature = _file_signature(path)
        if self._manifest.get(rel) == signature:
            return 0

        text = extract_text(path)
        if not text.strip():
            return 0

        count = await self._rag.index_document(
            doc_id=rel.replace("/", "__"),
            text=text,
            metadata={"source_path": rel, "filename": path.name},
        )
        self._manifest[rel] = signature
        self._save_manifest()
        logger.info("Indexed %s (%d chunks)", rel, count)
        return count

    async def sync_all(self) -> dict[str, int]:
        indexed = 0
        chunks = 0
        for path in self.discover_files():
            try:
                count = await self.index_file(path)
                if count:
                    indexed += 1
                    chunks += count
            except Exception as exc:  # noqa: BLE001
                logger.warning("Failed to index %s: %s", path, exc)
        return {"files_indexed": indexed, "chunks_indexed": chunks}


async def run_startup_indexer(rag_pipeline: Any) -> dict[str, int]:
    if os.environ.get("NEOMETIS_AUTO_INDEX", "true").lower() not in {"1", "true", "yes"}:
        return {"files_indexed": 0, "chunks_indexed": 0}
    indexer = WorkspaceDocIndexer(rag_pipeline)
    return await indexer.sync_all()


async def run_background_rescan(rag_pipeline: Any, interval_seconds: int = 60) -> None:
    """Periodic rescan for dropped-in files while the app is running."""
    if interval_seconds <= 0:
        return
    while True:
        await asyncio.sleep(interval_seconds)
        try:
            stats = await run_startup_indexer(rag_pipeline)
            if stats["files_indexed"]:
                logger.info("Background doc sync: %s", stats)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Background doc sync failed: %s", exc)
