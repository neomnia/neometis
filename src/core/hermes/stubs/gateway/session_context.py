"""Gateway stubs — messaging layer removed in NéoMêtis."""

from __future__ import annotations

import os


def get_session_env(key: str, default: str = "") -> str:
    return os.environ.get(key, default)
