"""Tests for CoreEngine end-to-end flow."""

import pytest

from beacon.core import (
    Context,
    ContextBuilder,
    CoreEngine,
    Dispatcher,
    Event,
    LLMRequest,
    Reaction,
    ReactionEngine,
)


class TestReaction(Reaction):
    """Simple test reaction for end-to-end testing."""

    @property
    def triggers_on(self) -> list[str]:
        return ["message"]

    def match(self, event: Event) -> bool:
        return "text" in event.payload

    async def produce(self, event: Event, ctx: Context) -> list[LLMRequest]:
        return [
            LLMRequest(
                conversation_id=ctx.conversation_id,
                actor_id=ctx.actor_id,
                messages=[{"role": "user", "content": event.payload["text"]}],
            )
        ]


@pytest.mark.asyncio
async def test_core_engine_end_to_end() -> None:
    """Test full CoreEngine flow: event → context → reaction → dispatch."""
    dispatched_requests: list[LLMRequest] = []

    async def mock_send_handler(request: LLMRequest) -> None:
        dispatched_requests.append(request)

    reactions = [TestReaction()]
    reaction_engine = ReactionEngine(reactions)
    context_builder = ContextBuilder()
    dispatcher = Dispatcher(send_handler=mock_send_handler)
    core_engine = CoreEngine(reaction_engine, context_builder, dispatcher)

    event = Event(
        type="message",
        source="matrix",
        payload={
            "text": "Hello from test",
            "room": "!test:example.com",
            "sender": "user:example.com",
        },
    )

    await core_engine.handle_event(event)

    # Verify request was dispatched
    assert len(dispatched_requests) == 1
    request = dispatched_requests[0]
    assert request.conversation_id == "!test:example.com"
    assert request.actor_id == "user:example.com"
    assert request.messages[0]["content"] == "Hello from test"


@pytest.mark.asyncio
async def test_core_engine_no_matching_reaction() -> None:
    """Test CoreEngine when no reactions match."""
    dispatched_requests: list[LLMRequest] = []

    async def mock_send_handler(request: LLMRequest) -> None:
        dispatched_requests.append(request)

    reactions = [TestReaction()]
    reaction_engine = ReactionEngine(reactions)
    context_builder = ContextBuilder()
    dispatcher = Dispatcher(send_handler=mock_send_handler)
    core_engine = CoreEngine(reaction_engine, context_builder, dispatcher)

    # Event without 'text' in payload (won't match TestReaction)
    event = Event(
        type="message",
        source="matrix",
        payload={"room": "!test:example.com", "sender": "user:example.com"},
    )

    await core_engine.handle_event(event)

    # No requests should be dispatched
    assert len(dispatched_requests) == 0


@pytest.mark.asyncio
async def test_core_engine_multiple_requests() -> None:
    """Test CoreEngine dispatching multiple requests from single event."""

    class MultiProducingReaction(Reaction):
        @property
        def triggers_on(self) -> list[str]:
            return ["multi"]

        def match(self, event: Event) -> bool:
            return True

        async def produce(self, event: Event, ctx: Context) -> list[LLMRequest]:
            # Produce 3 requests
            return [
                LLMRequest(
                    conversation_id=ctx.conversation_id,
                    actor_id=ctx.actor_id,
                    messages=[{"role": "user", "content": f"Request {i}"}],
                )
                for i in range(3)
            ]

    dispatched_requests: list[LLMRequest] = []

    async def mock_send_handler(request: LLMRequest) -> None:
        dispatched_requests.append(request)

    reactions = [MultiProducingReaction()]
    reaction_engine = ReactionEngine(reactions)
    context_builder = ContextBuilder()
    dispatcher = Dispatcher(send_handler=mock_send_handler)
    core_engine = CoreEngine(reaction_engine, context_builder, dispatcher)

    event = Event(
        type="multi",
        source="test",
        payload={"room": "!test:example.com", "sender": "user:example.com"},
    )

    await core_engine.handle_event(event)

    # All 3 requests should be dispatched
    assert len(dispatched_requests) == 3
