"""
Bridge between Nous Research Hermes Agent and NéoMêtis SSE transport.

When ``HERMES_UPSTREAM=1`` and vendored modules are present under
``src/core/hermes/upstream/``, this adapter delegates to the upstream
``AIAgent`` / ``conversation_loop`` stack. Otherwise it falls back to
:class:`~src.core.hermes.loop.LeanHermesLoop`.
"""

from __future__ import annotations

import logging
import os
from collections.abc import AsyncGenerator
from typing import Any

from src.core.hermes.events import AgentEvent, EventType
from src.core.hermes.loop import LeanHermesLoop, Tool

logger = logging.getLogger(__name__)

_UPSTREAM_ENABLED = os.environ.get("HERMES_UPSTREAM", "").strip() in {
    "1",
    "true",
    "yes",
}


def upstream_available() -> bool:
    """True when vendored Hermes modules can be imported."""
    if not _UPSTREAM_ENABLED:
        return False
    try:
        from src.core.hermes import upstream  # noqa: F401

        return upstream.is_available()
    except ImportError:
        return False


class HermesEngineAdapter:
    """Unified entry point for the Hermes reasoning engine in NéoMêtis."""

    def __init__(
        self,
        tools: list[Tool] | None = None,
        max_steps: int = 8,
        model: str | None = None,
        base_url: str | None = None,
        api_key: str | None = None,
    ) -> None:
        self._tools = tools or []
        self._max_steps = max_steps
        self._model = model or os.environ.get("HERMES_MODEL_NAME", "")
        self._base_url = base_url or os.environ.get("HERMES_API_BASE_URL", "")
        self._api_key = api_key or os.environ.get("HERMES_API_KEY", "")
        self._fallback = LeanHermesLoop(tools=self._tools, max_steps=max_steps)
        self._upstream_agent: Any | None = None

        if upstream_available():
            self._upstream_agent = self._build_upstream_agent()

    def _build_upstream_agent(self) -> Any:
        from src.core.hermes.upstream import create_agent

        return create_agent(
            tools=self._tools,
            model=self._model,
            base_url=self._base_url,
            api_key=self._api_key,
        )

    @property
    def engine_mode(self) -> str:
        return "upstream" if self._upstream_agent is not None else "lean"

    async def run(self, user_message: str) -> AsyncGenerator[AgentEvent, None]:
        if self._upstream_agent is None:
            async for event in self._fallback.run(user_message):
                yield event
            return

        try:
            from src.core.hermes.stream_bridge import bridge_upstream_stream

            async for event in bridge_upstream_stream(
                self._upstream_agent,
                user_message,
            ):
                yield event
        except Exception as exc:  # noqa: BLE001
            logger.exception("Upstream Hermes run failed; falling back to lean loop")
            yield AgentEvent(
                type=EventType.ERROR,
                content=f"Upstream Hermes error: {exc}",
                metadata={"fallback": True},
            )
            async for event in self._fallback.run(user_message):
                yield event
