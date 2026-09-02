"""
Lean Hermes ReAct loop (NéoMêtis-native fallback).

Used when upstream Hermes Agent code is not vendored yet. Mirrors the event
sequence produced by ``agent/conversation_loop.py`` in NousResearch/hermes-agent
so the FastAPI SSE layer stays stable during integration.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator, Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from src.core.hermes.events import AgentEvent, EventType


@dataclass(slots=True)
class Tool:
    """OpenAI/Hermes-compatible function-calling tool."""

    name: str
    description: str
    parameters: dict[str, Any]
    handler: Callable[..., Awaitable[Any]]

    def to_schema(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


class LeanHermesLoop:
    """Minimal async ReAct loop with native function calling."""

    def __init__(
        self,
        tools: list[Tool] | None = None,
        max_steps: int = 8,
        system_prompt: str = (
            "You are Hermes, the reasoning engine of NéoMêtis. "
            "Think step by step, call tools when useful, and answer concisely."
        ),
    ) -> None:
        self.tools = tools or []
        self.max_steps = max_steps
        self.system_prompt = system_prompt

    def _find_tool(self, name: str) -> Tool | None:
        return next((tool for tool in self.tools if tool.name == name), None)

    async def run(self, user_message: str) -> AsyncGenerator[AgentEvent, None]:
        yield AgentEvent(
            type=EventType.THOUGHT,
            content=f"Analyzing request: {user_message!r}",
        )

        for step in range(self.max_steps):
            decision = await self._think(user_message, step)

            if decision.get("action") == "tool_call":
                tool_name = decision["tool_name"]
                tool_args = decision.get("tool_args", {})
                tool = self._find_tool(tool_name)

                yield AgentEvent(
                    type=EventType.TOOL_CALL,
                    content=tool_name,
                    metadata={"arguments": tool_args},
                )

                if tool is None:
                    yield AgentEvent(
                        type=EventType.ERROR,
                        content=f"Unknown tool requested: {tool_name}",
                    )
                    break

                try:
                    result = await tool.handler(**tool_args)
                except Exception as exc:  # noqa: BLE001 - surfaced to the client
                    yield AgentEvent(type=EventType.ERROR, content=str(exc))
                    break

                yield AgentEvent(
                    type=EventType.TOOL_RESULT,
                    content=str(result),
                    metadata={"tool_name": tool_name},
                )
                continue

            yield AgentEvent(
                type=EventType.FINAL_ANSWER,
                content=decision.get("content", ""),
            )
            return

        yield AgentEvent(
            type=EventType.ERROR,
            content="Maximum number of reasoning steps reached without a final answer.",
        )

    async def _think(self, user_message: str, step: int) -> dict[str, Any]:
        return {
            "action": "final_answer",
            "content": (
                "Hermes upstream engine not vendored. "
                "Run scripts/vendor-hermes.sh then set HERMES_UPSTREAM=1. "
                f"Echoing input: {user_message}"
            ),
        }
