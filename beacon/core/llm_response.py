"""
LLM Response model: input from external LLM system.

This model is received by the ResponseAdapter and converted to an Event
for re-injection into the event bus.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class LLMResponse:
    """
    Response from an external LLM system.

    Attributes:
        request_id: Which request this response answers
        output: The LLM response data (text, structured, etc.)
        metadata: Response metadata (model used, tokens, latency, etc.)
    """

    request_id: str
    output: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
