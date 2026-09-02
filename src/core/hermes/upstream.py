"""
Vendored Hermes Agent upstream loader with headless stubs for stripped modules.
"""

from __future__ import annotations

import importlib.util
import logging
import os
import sys
from pathlib import Path
from typing import Any

from src.core.hermes.loop import Tool
from src.core.hermes.stubs import install_agent_stubs, install_tool_stubs, install_upstream_stubs

logger = logging.getLogger(__name__)

_UPSTREAM_DIR = Path(__file__).resolve().parent / "upstream"
_VENDORED_MARKER = _UPSTREAM_DIR / ".vendored"
_RUN_AGENT_MODULE = "neometis_hermes_run_agent"
_AIAgent: type[Any] | None = None
_LOAD_ERROR: str | None = None


def is_available() -> bool:
    """True when the vendor script has populated upstream modules."""
    return _VENDORED_MARKER.is_file() and (_UPSTREAM_DIR / "run_agent.py").is_file()


def vendored_metadata() -> dict[str, str]:
    if not _VENDORED_MARKER.is_file():
        return {}
    meta: dict[str, str] = {}
    for line in _VENDORED_MARKER.read_text(encoding="utf-8").splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            meta[key.strip()] = value.strip()
    return meta


def _ensure_upstream_path() -> None:
    upstream_str = str(_UPSTREAM_DIR)
    if upstream_str not in sys.path:
        sys.path.insert(0, upstream_str)


def _try_load_ai_agent_class() -> type[Any] | None:
    global _AIAgent, _LOAD_ERROR
    if _AIAgent is not None:
        return _AIAgent
    if _LOAD_ERROR is not None:
        return None

    if not is_available():
        _LOAD_ERROR = "not vendored"
        return None

    try:
        install_upstream_stubs()
        _ensure_upstream_path()
        install_tool_stubs()
        install_agent_stubs()

        spec = importlib.util.spec_from_file_location(
            _RUN_AGENT_MODULE,
            _UPSTREAM_DIR / "run_agent.py",
        )
        if spec is None or spec.loader is None:
            raise ImportError("Could not load vendored run_agent.py")

        module = importlib.util.module_from_spec(spec)
        sys.modules[_RUN_AGENT_MODULE] = module
        spec.loader.exec_module(module)

        ai_agent_cls = getattr(module, "AIAgent", None)
        if ai_agent_cls is None:
            raise ImportError("Vendored run_agent.py has no AIAgent class")

        _AIAgent = ai_agent_cls
        return _AIAgent
    except Exception as exc:  # noqa: BLE001
        _LOAD_ERROR = str(exc)
        logger.warning("Full upstream AIAgent load deferred: %s", exc)
        return None


class VendoredHermesAgent:
    """Headless wrapper around upstream ``AIAgent`` (lazy) for NéoMêtis SSE transport."""

    def __init__(
        self,
        tools: list[Tool] | None = None,
        model: str = "",
        base_url: str = "",
        api_key: str = "",
    ) -> None:
        os.environ.setdefault("HERMES_QUIET", "1")
        os.environ.setdefault("HERMES_NO_TUI", "1")
        os.environ.setdefault("NEOMETIS_HEADLESS", "1")

        self._tools = tools or []
        self._model = model
        self._base_url = base_url
        self._api_key = api_key
        self._agent: Any | None = None
        self._meta = vendored_metadata()

    @property
    def load_error(self) -> str | None:
        return _LOAD_ERROR

    def _ensure_agent(self) -> Any | None:
        if self._agent is not None:
            return self._agent

        ai_agent_cls = _try_load_ai_agent_class()
        if ai_agent_cls is None:
            return None

        kwargs: dict[str, Any] = {}
        if self._base_url:
            kwargs["base_url"] = self._base_url
        if self._model:
            kwargs["model"] = self._model
        if self._api_key:
            kwargs["api_key"] = self._api_key

        self._agent = ai_agent_cls(**kwargs)
        return self._agent

    def run_conversation(self, user_message: str) -> str:
        agent = self._ensure_agent()
        if agent is not None:
            return agent.run_conversation(user_message)

        ref = self._meta.get("ref", "unknown")
        return (
            f"[NéoMêtis upstream mode] Hermes engine vendored @ {ref}. "
            f"Full AIAgent runtime requires provider credentials and extended deps. "
            f"Message received: {user_message}"
        )


def create_agent(
    tools: list[Tool] | None = None,
    model: str = "",
    base_url: str = "",
    api_key: str = "",
) -> VendoredHermesAgent:
    """Instantiate headless upstream Hermes agent."""
    return VendoredHermesAgent(
        tools=tools,
        model=model,
        base_url=base_url,
        api_key=api_key,
    )
