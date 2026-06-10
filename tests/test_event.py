"""Tests for Event model."""

from beacon.core import Event


def test_event_creation() -> None:
    """Test basic Event instantiation."""
    event = Event(type="message", source="matrix", payload={"text": "hello"})

    assert event.type == "message"
    assert event.source == "matrix"
    assert event.payload == {"text": "hello"}
    assert event.id is not None
    assert event.timestamp is not None


def test_event_metadata_defaults() -> None:
    """Test that Event initializes default metadata."""
    event = Event(type="test", source="test")

    assert "hop_count" in event.metadata
    assert "correlation_id" in event.metadata
    assert event.metadata["hop_count"] == 0
    assert event.metadata["correlation_id"] == event.id


def test_event_metadata_preserves_custom() -> None:
    """Test that Event preserves custom metadata."""
    custom_meta = {"custom_key": "custom_value", "hop_count": 2}
    event = Event(type="test", source="test", metadata=custom_meta)

    assert event.metadata["custom_key"] == "custom_value"
    assert event.metadata["hop_count"] == 2  # Custom value preserved
    assert "correlation_id" in event.metadata  # But correlation_id still added


def test_event_unique_ids() -> None:
    """Test that each Event gets a unique ID."""
    event1 = Event(type="test", source="test")
    event2 = Event(type="test", source="test")

    assert event1.id != event2.id
