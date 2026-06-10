"""
Context model: encapsulates conversation state and metadata.

Context is built per-event and passed through the reaction engine.
It must be stateless and derived solely from the event.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class Context:
    """
    Immutable context for event processing.

    Attributes:
        conversation_id: Identifier for the ongoing conversation/thread
        actor_id: Identifier for the entity triggering the event (user, room, etc.)
        history: Recent event history (optional, for context)
        metadata: Additional system metadata (timestamp, environment, etc.)
        memory: Optional persistent or session memory (consumer-filled)
    """

    conversation_id: str
    actor_id: str
    history: list[Any] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    memory: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Ensure metadata has required fields."""
        if "timestamp" not in self.metadata:
            self.metadata["timestamp"] = datetime.now(timezone.utc)
