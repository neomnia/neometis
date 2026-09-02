"""In-memory session stub replacing hermes_state SQLite in headless mode."""

from __future__ import annotations

from typing import Any


class _StubDB:
    def close(self) -> None:
        return None


def get_shared_session_db(*args: Any, **kwargs: Any) -> _StubDB:
    return _StubDB()


def release_or_close(*args: Any, **kwargs: Any) -> None:
    return None
