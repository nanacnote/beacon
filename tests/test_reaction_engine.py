"""Tests for ReactionEngine and Reaction interface."""

import pytest

from beacon.core import Context, Event, LLMRequest, Reaction, ReactionEngine


class SimpleMessageReaction(Reaction):
    """Test reaction that converts messages to LLMRequests."""

    @property
    def triggers_on(self) -> list[str]:
        return ["message"]

    def match(self, event: Event) -> bool:
        # Only match if payload has 'text'
        return "text" in event.payload

    async def produce(self, event: Event, ctx: Context) -> list[LLMRequest]:
        request = LLMRequest(
            conversation_id=ctx.conversation_id,
            actor_id=ctx.actor_id,
            messages=[{"role": "user", "content": event.payload["text"]}],
        )
        return [request]


class TimerReaction(Reaction):
    """Test reaction that processes timer events."""

    @property
    def triggers_on(self) -> list[str]:
        return ["timer"]

    def match(self, event: Event) -> bool:
        return True

    async def produce(self, event: Event, ctx: Context) -> list[LLMRequest]:
        # Timer events produce no requests
        return []


@pytest.mark.asyncio
async def test_reaction_engine_filters_by_triggers_on() -> None:
    """Test that ReactionEngine filters by triggers_on."""
    reactions = [SimpleMessageReaction(), TimerReaction()]
    engine = ReactionEngine(reactions)

    ctx = Context(conversation_id="room1", actor_id="user1")

    # Message event should match only SimpleMessageReaction
    message_event = Event(
        type="message",
        source="test",
        payload={"text": "Hello"},
    )

    requests = await engine.process(message_event, ctx)

    # Should get 1 request from SimpleMessageReaction
    assert len(requests) == 1
    assert requests[0].messages[0]["content"] == "Hello"


@pytest.mark.asyncio
async def test_reaction_engine_aggregates_requests() -> None:
    """Test that ReactionEngine aggregates requests from multiple reactions."""

    class MultiReaction1(Reaction):
        @property
        def triggers_on(self) -> list[str]:
            return ["test"]

        def match(self, event: Event) -> bool:
            return True

        async def produce(self, event: Event, ctx: Context) -> list[LLMRequest]:
            return [
                LLMRequest(
                    conversation_id=ctx.conversation_id,
                    actor_id=ctx.actor_id,
                    messages=[{"role": "user", "content": "Request 1"}],
                )
            ]

    class MultiReaction2(Reaction):
        @property
        def triggers_on(self) -> list[str]:
            return ["test"]

        def match(self, event: Event) -> bool:
            return True

        async def produce(self, event: Event, ctx: Context) -> list[LLMRequest]:
            return [
                LLMRequest(
                    conversation_id=ctx.conversation_id,
                    actor_id=ctx.actor_id,
                    messages=[{"role": "user", "content": "Request 2"}],
                )
            ]

    reactions = [MultiReaction1(), MultiReaction2()]
    engine = ReactionEngine(reactions)

    ctx = Context(conversation_id="room1", actor_id="user1")
    event = Event(type="test", source="test", payload={})

    requests = await engine.process(event, ctx)

    # Should get 2 requests, one from each reaction
    assert len(requests) == 2
    assert requests[0].messages[0]["content"] == "Request 1"
    assert requests[1].messages[0]["content"] == "Request 2"


@pytest.mark.asyncio
async def test_reaction_engine_respects_match() -> None:
    """Test that ReactionEngine respects reaction match() function."""

    class SelectiveReaction(Reaction):
        @property
        def triggers_on(self) -> list[str]:
            return ["message"]

        def match(self, event: Event) -> bool:
            # Only match if sender is "alice"
            return event.payload.get("sender") == "alice"

        async def produce(self, event: Event, ctx: Context) -> list[LLMRequest]:
            return [
                LLMRequest(
                    conversation_id=ctx.conversation_id,
                    actor_id=ctx.actor_id,
                    messages=[{"role": "user", "content": "From alice"}],
                )
            ]

    reactions = [SelectiveReaction()]
    engine = ReactionEngine(reactions)

    ctx = Context(conversation_id="room1", actor_id="alice")

    # Event from alice should match
    event_alice = Event(
        type="message",
        source="test",
        payload={"sender": "alice", "text": "Hello"},
    )

    requests = await engine.process(event_alice, ctx)
    assert len(requests) == 1

    # Event from bob should not match
    event_bob = Event(
        type="message",
        source="test",
        payload={"sender": "bob", "text": "Hello"},
    )

    requests = await engine.process(event_bob, ctx)
    assert len(requests) == 0
