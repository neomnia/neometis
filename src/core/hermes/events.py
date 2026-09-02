"""SSE event types emitted by the NéoMêtis Hermes engine adapter."""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class EventType(str, Enum):
    """Types of events streamed while the agent thinks and acts."""

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
        """Serialize this event as a Server-Sent Events frame."""
        payload = {
            "id": self.id,
            "type": self.type.value,
            "content": self.content,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
        }
        return f"event: {self.type.value}\ndata: {json.dumps(payload)}\n\n"
