"""Hermes engine package — adapted from Nous Research Hermes Agent (MIT)."""

from src.core.hermes.adapter import HermesEngineAdapter, upstream_available
from src.core.hermes.events import AgentEvent, EventType
from src.core.hermes.loop import LeanHermesLoop, Tool

# Public alias used by the API layer and integration tests.
HermesAgent = HermesEngineAdapter

__all__ = [
    "AgentEvent",
    "EventType",
    "HermesAgent",
    "HermesEngineAdapter",
    "LeanHermesLoop",
    "Tool",
    "upstream_available",
]
