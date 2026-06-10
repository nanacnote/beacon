"""Tests for ContextBuilder."""

import asyncio

import pytest

from beacon.core import ContextBuilder, Event


def test_context_builder_default_extraction() -> None:
    """Test default context builder extractors."""
    builder = ContextBuilder()

    event = Event(
        type="message",
        source="matrix",
        payload={"room": "!room:example.com", "sender": "user:example.com"},
    )

    ctx = asyncio.run(builder.build(event))

    assert ctx.conversation_id == "!room:example.com"
    assert ctx.actor_id == "user:example.com"


def test_context_builder_custom_extraction() -> None:
    """Test custom extraction functions."""

    def get_conv_id(event: Event) -> str:
        return f"conv-{event.payload.get('room')}"

    def get_actor_id(event: Event) -> str:
        return f"actor-{event.payload.get('sender')}"

    builder = ContextBuilder(
        conversation_extractor=get_conv_id,
        actor_extractor=get_actor_id,
    )

    event = Event(
        type="message",
        source="matrix",
        payload={"room": "123", "sender": "alice"},
    )

    ctx = asyncio.run(builder.build(event))

    assert ctx.conversation_id == "conv-123"
    assert ctx.actor_id == "actor-alice"


@pytest.mark.asyncio
async def test_context_builder_with_history_fetcher() -> None:
    """Test context builder with history fetching."""

    async def fetch_history(conv_id: str, actor_id: str) -> list:
        # Mock history
        return [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
        ]

    builder = ContextBuilder(history_fetcher=fetch_history)

    event = Event(
        type="message",
        source="matrix",
        payload={"room": "room1", "sender": "user1"},
    )

    ctx = await builder.build(event)

    assert len(ctx.history) == 2
    assert ctx.history[0]["role"] == "user"
