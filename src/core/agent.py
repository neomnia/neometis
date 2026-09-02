"""
Backward-compatible re-export.

New code should import from ``src.core.hermes`` directly.
"""

from src.core.hermes import (
    AgentEvent,
    EventType,
    HermesAgent,
    HermesEngineAdapter,
    LeanHermesLoop,
    Tool,
    upstream_available,
)

__all__ = [
    "AgentEvent",
    "EventType",
    "HermesAgent",
    "HermesEngineAdapter",
    "LeanHermesLoop",
    "Tool",
    "upstream_available",
]
