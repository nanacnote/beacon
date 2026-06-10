"""
Core domain models for the Reactive LLM Interface Layer.

This module defines the fundamental types: Event, Context, LLMRequest, and LLMResponse.
These types are transport-agnostic and form the contract between system components.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


@dataclass
class Event:
    """
    Normalized event from external message systems (or internal loop).

    Attributes:
        id: Unique event identifier
        type: Event classification (e.g., "message", "llm_response", "timer")
        source: Abstract source (e.g., "matrix", "internal")
        timestamp: Event creation time (UTC)
        payload: Event-specific data (e.g., message text, sender)
        metadata: System metadata (hop_count, correlation_id, etc.)
    """

    id: str = field(default_factory=lambda: str(uuid4()))
    type: str = ""
    source: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    payload: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Ensure required metadata fields exist."""
        if "hop_count" not in self.metadata:
            self.metadata["hop_count"] = 0
        if "correlation_id" not in self.metadata:
            self.metadata["correlation_id"] = self.id
