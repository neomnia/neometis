"""
Base definitions for NéoMêtis native tools.

Concrete tools (workspace file access, Penpot API sidecar, Plane.so API)
should subclass or instantiate :class:`~src.core.agent.Tool` using the
helpers below to keep function-calling schemas consistent.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from src.core.agent import Tool


def make_tool(
    name: str,
    description: str,
    parameters: dict[str, Any],
    handler: Callable[..., Awaitable[Any]],
) -> Tool:
    """Build a :class:`Tool` with an explicit JSON-schema parameter spec."""
    return Tool(
        name=name,
        description=description,
        parameters=parameters,
        handler=handler,
    )
