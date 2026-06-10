"""
Matrix Inbound Adapter: mautrix → EventBus.

Receives Matrix events from mautrix, converts via EventAdapter,
and publishes to EventBus. Supports multi-room operation.
"""

from typing import Optional

from beacon.adapters.event_adapter import EventAdapter
from beacon.infra.event_bus import EventBus


class MatrixAdapter:
    """
    Ingress adapter for Matrix (via mautrix) events.

    Responsibilities:
    - Receive mautrix-formatted events
    - Normalize via EventAdapter
    - Publish to EventBus
    - Multi-room aware
    """

    def __init__(self, event_bus: EventBus, event_adapter: Optional[EventAdapter] = None):
        """
        Initialize MatrixAdapter.

        Args:
            event_bus: EventBus to publish events to
            event_adapter: EventAdapter for normalization (default: EventAdapter)
        """
        self._event_bus = event_bus
        self._event_adapter = event_adapter or EventAdapter()

    async def ingest_room_message(
        self, room_id: str, sender: str, content: dict
    ) -> None:
        """
        Ingest a message event from a Matrix room.

        Args:
            room_id: Matrix room ID (e.g., "!room:example.com")
            sender: Matrix user ID (e.g., "@user:example.com")
            content: Message content dict (e.g., {"body": "Hello", "msgtype": "m.text"})
        """
        # Build raw event dict in mautrix-like format
        raw_event = {
            "type": "m.room.message",
            "sender": sender,
            "room_id": room_id,
            "content": content,
            "source": "matrix",
        }

        # Normalize
        event = self._event_adapter.from_external(raw_event)

        # Publish
        await self._event_bus.publish(event)

    async def ingest_raw_event(self, raw_event: dict) -> None:
        """
        Ingest a raw Matrix event (for more direct access).

        Args:
            raw_event: Raw Matrix event dict
        """
        raw_event["source"] = "matrix"
        event = self._event_adapter.from_external(raw_event)
        await self._event_bus.publish(event)
