"""
LLM Request model: output from reactions, input to dispatcher.

This model represents a request to an external LLM system.
Tool definitions are schemas only; no execution happens in this layer.
"""

from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4


@dataclass
class LLMRequest:
    """
    Normalized request to an LLM system.

    Attributes:
        id: Unique request identifier (for correlation with responses)
        conversation_id: Which conversation this request belongs to
        actor_id: Who initiated the request (indirectly, via reaction)
        messages: List of message dicts (content, role, etc.)
        metadata: Request metadata (timestamp, model hint, etc.)
        hints: Optional guidance for LLM (e.g., "be concise", "return JSON")
        tools: List of tool schema dicts (not executed, for LLM awareness)
    """

    id: str = field(default_factory=lambda: str(uuid4()))
    conversation_id: str = ""
    actor_id: str = ""
    messages: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    hints: dict[str, Any] = field(default_factory=dict)
    tools: list[dict[str, Any]] = field(default_factory=list)
