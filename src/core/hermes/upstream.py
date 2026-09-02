"""
Vendored Hermes Agent upstream loader.

After running ``scripts/vendor-hermes.sh``, selected modules from
``NousResearch/hermes-agent`` are copied into ``upstream/``. This module
exposes a minimal factory that strips CLI/TUI/gateway dependencies and
returns an ``AIAgent`` configured for headless API use.
"""

from __future__ import annotations

import importlib.util
import logging
import os
from pathlib import Path
from typing import Any

from src.core.hermes.loop import Tool

logger = logging.getLogger(__name__)

_UPSTREAM_DIR = Path(__file__).resolve().parent / "upstream"
_VENDORED_MARKER = _UPSTREAM_DIR / ".vendored"


def is_available() -> bool:
    """True when the vendor script has populated upstream modules."""
    return _VENDORED_MARKER.is_file() and (_UPSTREAM_DIR / "run_agent.py").is_file()


def create_agent(
    tools: list[Tool] | None = None,
    model: str = "",
    base_url: str = "",
    api_key: str = "",
) -> Any:
    """Instantiate upstream ``AIAgent`` without CLI or gateway transports."""
    if not is_available():
        raise RuntimeError(
            "Hermes upstream not vendored. Run: ./scripts/vendor-hermes.sh"
        )

    # Ensure vendored tree is importable as top-level modules (mirrors upstream layout).
    import sys

    upstream_str = str(_UPSTREAM_DIR)
    if upstream_str not in sys.path:
        sys.path.insert(0, upstream_str)

    spec = importlib.util.spec_from_file_location(
        "neometis_hermes_run_agent",
        _UPSTREAM_DIR / "run_agent.py",
    )
    if spec is None or spec.loader is None:
        raise ImportError("Could not load vendored run_agent.py")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    AIAgent = getattr(module, "AIAgent", None)
    if AIAgent is None:
        raise ImportError("Vendored run_agent.py has no AIAgent class")

    kwargs: dict[str, Any] = {}
    if base_url:
        kwargs["base_url"] = base_url
    if model:
        kwargs["model"] = model
    if api_key:
        kwargs["api_key"] = api_key

    agent = AIAgent(**kwargs)

    # Disable display/TUI output — NéoMêtis streams via SSE instead.
    os.environ.setdefault("HERMES_QUIET", "1")
    os.environ.setdefault("HERMES_NO_TUI", "1")

    if tools:
        logger.info("Registering %d NéoMêtis-native tools with upstream agent", len(tools))
        # Tool registration hook point — wire neometis tools into upstream registry
        # once vendor-hermes.sh copies model_tools.py + tools/registry.py.

    return agent
