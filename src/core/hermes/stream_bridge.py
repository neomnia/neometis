"""
Maps upstream Hermes Agent streaming callbacks to NéoMêtis :class:`AgentEvent`.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator
from typing import Any

from src.core.hermes.events import AgentEvent, EventType


async def bridge_upstream_stream(
    agent: Any,
    user_message: str,
) -> AsyncGenerator[AgentEvent, None]:
    """Run upstream ``AIAgent.run_conversation`` and yield normalized SSE events."""
    queue: asyncio.Queue[AgentEvent | None] = asyncio.Queue()
    loop = asyncio.get_running_loop()

    def _emit(event_type: EventType, content: str, metadata: dict | None = None) -> None:
        loop.call_soon_threadsafe(
            queue.put_nowait,
            AgentEvent(type=event_type, content=content, metadata=metadata or {}),
        )

    def _run_sync() -> None:
        try:
            _emit(EventType.THOUGHT, f"Starting Hermes upstream run for: {user_message!r}")

            if hasattr(agent, "run_conversation"):
                response = agent.run_conversation(user_message)
            elif hasattr(agent, "run"):
                response = agent.run(user_message)
            else:
                raise RuntimeError("Upstream agent has no run_conversation/run method")

            _emit(EventType.FINAL_ANSWER, str(response))
        except Exception as exc:  # noqa: BLE001
            _emit(EventType.ERROR, str(exc))
        finally:
            loop.call_soon_threadsafe(queue.put_nowait, None)

    executor_task = loop.run_in_executor(None, _run_sync)

    while True:
        item = await queue.get()
        if item is None:
            break
        yield item

    await executor_task
