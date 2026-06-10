"""
Example: Single-room event flow.

Demonstrates the full Beacon loop:
1. Matrix message event enters system
2. Converted to Event via adapter
3. Processed through reaction engine
4. LLMRequest dispatched to mock LLM
5. Response received and re-injected
6. Loop continues
"""

import asyncio

from beacon.adapters.inbound.matrix import MatrixAdapter
from beacon.adapters.response.llm_response import ResponseAdapter
from beacon.core import ContextBuilder, CoreEngine, ReactionEngine
from beacon.core.dispatcher import Dispatcher
from beacon.infra import EventBus
from beacon.infra.mock_dispatcher import MockDispatcher
from beacon.reactions import MessageToLLMReaction


async def main() -> None:
    """
    Run a single message through the full loop.
    """
    print("=== Beacon Event Loop Demo ===\n")

    # 1. Create EventBus
    event_bus = EventBus(max_workers=2)
    await event_bus.start()

    # 2. Create adapters
    matrix_adapter = MatrixAdapter(event_bus)
    response_adapter = ResponseAdapter(event_bus)

    # 3. Create reactions
    reactions = [MessageToLLMReaction()]
    reaction_engine = ReactionEngine(reactions)

    # 4. Create dispatcher (with mock LLM response callback)
    async def mock_llm_response_callback(response):
        """Handle mock LLM response by re-injecting as event."""
        print(f"\n[LLM Response] Request {response.request_id}:")
        print(f"  Content: {response.output.get('content')}")
        await response_adapter.handle_response(response)

    mock_dispatcher = MockDispatcher(
        delay_seconds=0.5,
        response_callback=mock_llm_response_callback,
    )

    # 5. Create real dispatcher wrapper
    async def dispatcher_send_handler(request):
        """Forward to mock dispatcher."""
        await mock_dispatcher.dispatch(request)

    real_dispatcher = Dispatcher(send_handler=dispatcher_send_handler)

    # 6. Create context builder and core engine
    context_builder = ContextBuilder()
    core_engine = CoreEngine(reaction_engine, context_builder, real_dispatcher)

    async def message_handler(event):
        """Route message events through the core engine."""
        await core_engine.handle_event(event)

    event_bus.subscribe("message", message_handler)

    # 7. Set up event handlers
    async def llm_response_handler(event):
        """Demonstrate second reaction to LLM responses."""
        print(f"\n[Event Handler] Received {event.type} event:")
        print(f"  Request ID: {event.payload.get('request_id')}")
        print(f"  Response: {event.payload.get('output')}")

    event_bus.subscribe("llm_response", llm_response_handler)

    # 8. Send a Matrix message
    print("1. Ingesting Matrix message...\n")
    await matrix_adapter.ingest_room_message(
        room_id="!demo:example.com",
        sender="@alice:example.com",
        content={"body": "Hello, Beacon!", "msgtype": "m.text"},
    )

    # Wait for processing
    await asyncio.sleep(2)

    # 9. Send another message to show multi-message flow
    print("\n2. Ingesting second Matrix message...\n")
    await matrix_adapter.ingest_room_message(
        room_id="!demo:example.com",
        sender="@bob:example.com",
        content={"body": "How are you?", "msgtype": "m.text"},
    )

    # Wait for processing
    await asyncio.sleep(2)

    # Cleanup
    await event_bus.stop()

    print("\n=== Demo Complete ===")


if __name__ == "__main__":
    asyncio.run(main())
