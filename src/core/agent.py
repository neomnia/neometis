"""
NéoMêtis Core Agent
====================

Minimal implementation of the Hermes ReAct loop: a "Reason + Act" agentic
loop with native function calling, designed to stream its reasoning and
tool calls in real time over Server-Sent Events (SSE).

This module is intentionally self-contained and dependency-light so it can
be swapped out for a full Hermes engine integration later without touching
the FastAPI transport layer in ``src/api/main.py``.
"""

from __future__ import annotations

import json
import time
import uuid
from collections.abc import AsyncGenerator, Awaitable, Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class EventType(str, Enum):
    """Types of events emitted while the agent thinks and acts."""

    THOUGHT = "thought"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    TOKEN = "token"
    FINAL_ANSWER = "final_answer"
    ERROR = "error"


@dataclass(slots=True)
class AgentEvent:
    """A single unit of streamed agent output."""

    type: EventType
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: uuid.uuid4().hex)
    timestamp: float = field(default_factory=time.time)

    def to_sse(self) -> str:
        """Serialize this event as a Server-Sent Events ``data:`` frame."""
        payload = {
            "id": self.id,
            "type": self.type.value,
            "content": self.content,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
        }
        return f"event: {self.type.value}\ndata: {json.dumps(payload)}\n\n"


@dataclass(slots=True)
class Tool:
    """A function-calling tool exposed to the agent."""

    name: str
    description: str
    parameters: dict[str, Any]
    handler: Callable[..., Awaitable[Any]]

    def to_schema(self) -> dict[str, Any]:
        """OpenAI/Hermes-compatible function-calling schema for this tool."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


class HermesAgent:
    """A minimal Hermes-style ReAct agent.

    The agent runs a bounded loop of: *think* -> *act* (optional tool call)
    -> *observe* -> repeat, until a final answer is produced or the maximum
    number of steps is reached. Every step yields :class:`AgentEvent`
    instances so callers (e.g. the FastAPI SSE endpoint) can stream progress
    to the client in real time.
    """

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
        """Execute the ReAct loop for ``user_message``, streaming events.

        This reference implementation does not call an LLM directly; it is
        the wiring point where a real Hermes model client should be plugged
        in (see the ``_think`` method below). It demonstrates the expected
        event sequence: thought -> tool_call -> tool_result -> final_answer.
        """
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
        """Decide the next action: call a tool or answer directly.

        Placeholder reasoning: plug in a real Hermes/LLM call here. It must
        return either ``{"action": "tool_call", "tool_name": ..., "tool_args": {...}}``
        or ``{"action": "final_answer", "content": "..."}``.
        """
        return {
            "action": "final_answer",
            "content": (
                "Hermes engine not yet connected. "
                f"Echoing input: {user_message}"
            ),
        }
