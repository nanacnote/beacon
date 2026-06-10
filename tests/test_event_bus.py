"""Tests for EventBus async queue and worker pool."""

import asyncio

import pytest

from beacon.core import Event
from beacon.infra import EventBus


@pytest.mark.asyncio
async def test_event_bus_publish_subscribe() -> None:
    """Test basic publish and subscribe without workers."""
    bus = EventBus()
    received_events: list[Event] = []

    async def handler(event: Event) -> None:
        received_events.append(event)

    # Subscribe before publishing
    bus.subscribe("message", handler)

    # Publish event
    event = Event(type="message", source="test", payload={"text": "hello"})
    await bus.publish(event)

    # Start bus and let it process
    await bus.start()
    await asyncio.sleep(0.1)  # Allow worker to process
    await bus.stop()

    assert len(received_events) == 1
    assert received_events[0].id == event.id


@pytest.mark.asyncio
async def test_event_bus_multiple_handlers() -> None:
    """Test multiple handlers for same event type."""
    bus = EventBus()
    count = {"handler1": 0, "handler2": 0}

    async def handler1(event: Event) -> None:
        count["handler1"] += 1

    async def handler2(event: Event) -> None:
        count["handler2"] += 1

    bus.subscribe("message", handler1)
    bus.subscribe("message", handler2)

    event = Event(type="message", source="test")
    await bus.publish(event)

    await bus.start()
    await asyncio.sleep(0.1)
    await bus.stop()

    assert count["handler1"] == 1
    assert count["handler2"] == 1


@pytest.mark.asyncio
async def test_event_bus_wildcard_handler() -> None:
    """Test wildcard subscription to all event types."""
    bus = EventBus()
    received_types: list[str] = []

    async def wildcard_handler(event: Event) -> None:
        received_types.append(event.type)

    bus.subscribe("*", wildcard_handler)

    # Publish different event types
    await bus.publish(Event(type="message", source="test"))
    await bus.publish(Event(type="timer", source="test"))
    await bus.publish(Event(type="llm_response", source="test"))

    await bus.start()
    await asyncio.sleep(0.1)
    await bus.stop()

    assert len(received_types) == 3
    assert "message" in received_types
    assert "timer" in received_types
    assert "llm_response" in received_types


@pytest.mark.asyncio
async def test_event_bus_concurrent_publishes() -> None:
    """Test multiple concurrent publishes."""
    bus = EventBus()
    received_events: list[Event] = []

    async def handler(event: Event) -> None:
        received_events.append(event)

    bus.subscribe("test", handler)

    # Publish multiple events concurrently
    await asyncio.gather(
        *[
            bus.publish(Event(type="test", source="test", payload={"id": i}))
            for i in range(10)
        ]
    )

    await bus.start()
    await asyncio.sleep(0.2)
    await bus.stop()

    assert len(received_events) == 10


@pytest.mark.asyncio
async def test_event_bus_queue_full() -> None:
    """Test behavior when queue is full (put_nowait raises)."""
    bus = EventBus(max_workers=1, queue_size=2)

    # Pause the worker to fill up the queue
    await bus.start()

    # Fill the queue (bypassing put_nowait will require direct access)
    await bus.publish(Event(type="test", source="test"))
    await bus.publish(Event(type="test", source="test"))

    # Third publish should raise QueueFull
    with pytest.raises(asyncio.QueueFull):
        await bus.publish(Event(type="test", source="test"))

    await bus.stop()


@pytest.mark.asyncio
async def test_event_bus_worker_pool_handles_exceptions() -> None:
    """Test that exceptions in handlers don't crash workers."""
    bus = EventBus()
    successful_events: list[Event] = []

    async def failing_handler(event: Event) -> None:
        raise ValueError("Handler failed")

    async def success_handler(event: Event) -> None:
        successful_events.append(event)

    bus.subscribe("test", failing_handler)
    bus.subscribe("test", success_handler)

    event = Event(type="test", source="test")
    await bus.publish(event)

    await bus.start()
    await asyncio.sleep(0.1)
    await bus.stop()

    # Success handler should still have been called
    assert len(successful_events) == 1
