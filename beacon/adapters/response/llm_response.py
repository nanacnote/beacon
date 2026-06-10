"""
Response Adapter: LLM responses → Event re-injection.

Accepts LLMResponse (from any transport), converts to Event,
and re-injects into EventBus for further processing.
"""

import logging

from beacon.core.event import Event
from beacon.core.llm_response import LLMResponse
from beacon.infra.event_bus import EventBus

logger = logging.getLogger(__name__)


class ResponseAdapter:
    """
    Egress adapter for LLM responses.

    Accepts LLMResponse objects from any transport (HTTP, queue, etc.),
    normalizes to Event, and re-injects into EventBus.

    The consumer is responsible for calling this adapter's methods
    from their chosen transport layer (HTTP webhook, queue consumer, etc.).
    """

    def __init__(self, event_bus: EventBus):
        """
        Initialize ResponseAdapter.

        Args:
            event_bus: EventBus to re-inject responses into
        """
        self._event_bus = event_bus

    async def handle_response(self, response: LLMResponse) -> None:
        """
        Process an LLM response and re-inject as event.

        Args:
            response: LLMResponse from external LLM system
        """
        # Convert to Event
        event = Event(
            type="llm_response",
            source="llm",
            payload={
                "request_id": response.request_id,
                "output": response.output,
            },
            metadata={
                    "hop_count": response.metadata.get("hop_count", 0),
                "correlation_id": response.metadata.get("correlation_id", response.request_id),
            },
        )

        logger.debug("Re-injecting LLM response as event request_id=%s", response.request_id)

        # Re-inject into event bus
        await self._event_bus.publish(event)

    async def handle_response_dict(self, response_dict: dict) -> None:
        """
        Convenience method: accept dict and convert to LLMResponse.

        Args:
            response_dict: Dict with keys: request_id, output, metadata
        """
        response = LLMResponse(
            request_id=response_dict["request_id"],
            output=response_dict.get("output", {}),
            metadata=response_dict.get("metadata", {}),
        )
        await self.handle_response(response)
