"""
Event Adapter: normalize external events to internal Event format.

This adapter ensures no transport-specific details leak into core logic.
"""

from typing import Any

from beacon.core.event import Event


class EventAdapter:
    """
    Bidirectional adapter for Event serialization/deserialization.

    from_external(): Raw external event → Event
    to_external(): Action/Event → Transport-specific format
    """

    @staticmethod
    def from_external(raw_event: dict[str, Any]) -> Event:
        """
        Convert external (e.g., Matrix) event to internal Event.

        Args:
            raw_event: Raw event dict from external system

        Returns:
            Event: Normalized internal Event

        Example:
            Matrix event:
            {
                "type": "m.room.message",
                "content": {"body": "Hello"},
                "sender": "@user:example.com",
                "room_id": "!room:example.com"
            }

            Becomes:
            Event(
                type="message",
                source="matrix",
                payload={"text": "Hello", "sender": "...", "room": "..."}
            )
        """
        # Extract type (transport-specific → generic)
        event_type = raw_event.get("event_type", "message")
        if "m.room.message" in raw_event.get("type", ""):
            event_type = "message"

        # Build normalized payload
        payload = {
            "text": raw_event.get("content", {}).get("body", ""),
            "sender": raw_event.get("sender", ""),
            "room": raw_event.get("room_id", ""),
            "raw": raw_event,  # Store original for reference
        }

        return Event(
            type=event_type,
            source=raw_event.get("source", "unknown"),
            payload=payload,
            metadata=raw_event.get("metadata", {}),
        )

    @staticmethod
    def to_external(action: dict[str, Any]) -> dict[str, Any]:
        """
        Convert action/response to transport-ready format.

        Args:
            action: Action dict (e.g., {"type": "send", "room": "...", "text": "..."})

        Returns:
            dict: Transport-ready format for dispatcher

        Example:
            action:
            {"type": "reply", "room": "!room:example.com", "text": "Response"}

            Becomes:
            {
                "msgtype": "m.text",
                "body": "Response",
                "room_id": "!room:example.com"
            }
        """
        # Map generic action to transport format
        if action.get("type") == "reply":
            return {
                "msgtype": "m.text",
                "body": action.get("text", ""),
                "room_id": action.get("room", ""),
            }

        return action
