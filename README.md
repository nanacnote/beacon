# Beacon

A production-oriented Python library for **transport-agnostic, event-driven LLM orchestration**.

Beacon normalizes inbound events, builds context, runs composable reactions, dispatches LLM requests asynchronously, and re-injects responses back into the event loop.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Install Matrix support when needed:

```bash
pip install -e ".[matrix]"
```

## Usage

### 1. Define one or more reactions

```python
from beacon.core import Context, Event, LLMRequest, Reaction


class MessageReaction(Reaction):
    @property
    def triggers_on(self) -> list[str]:
        return ["message"]

    def match(self, event: Event) -> bool:
        return bool(event.payload.get("text"))

    async def produce(self, event: Event, ctx: Context) -> list[LLMRequest]:
        return [
            LLMRequest(
                conversation_id=ctx.conversation_id,
                actor_id=ctx.actor_id,
                messages=[{"role": "user", "content": event.payload["text"]}],
                metadata={"source_event_id": event.id},
            )
        ]
```

### 2. Wire the engine and dispatcher

```python
import asyncio

from beacon.core import ContextBuilder, CoreEngine, Dispatcher, Event, ReactionEngine


async def send_handler(request):
    # HTTP, queue, or any external delivery mechanism
    print(f"Dispatching request: {request.id}")


async def main():
    reaction_engine = ReactionEngine([MessageReaction()])
    context_builder = ContextBuilder()
    dispatcher = Dispatcher(send_handler=send_handler)
    engine = CoreEngine(reaction_engine, context_builder, dispatcher)

    event = Event(
        type="message",
        source="demo",
        payload={"text": "Hello", "room": "room-1", "sender": "user-1"},
    )
    await engine.handle_event(event)


asyncio.run(main())
```

### 3. Run full loop example

```bash
python examples/single_room_flow.py
```

## Architecture

```
Inbound Adapter -> EventAdapter -> EventBus
                                  |
                                  v
                             CoreEngine
                     (ContextBuilder + ReactionEngine)
                                  |
                                  v
                              Dispatcher
                                  |
                                  v
                           External LLM System
                                  |
                                  v
                           ResponseAdapter
                                  |
                                  v
                                EventBus
```

Primary modules:

```
beacon/core/
|- event.py            # Event, Context, LLM request/response models
|- reaction.py         # Reaction interface
|- engine.py           # ReactionEngine and CoreEngine
|- dispatcher.py       # Async request dispatch boundary
|- context_builder.py  # Event -> Context mapping
|- controls.py         # Hop, idempotency, and rate controls

beacon/adapters/
|- event_adapter.py
|- inbound/matrix.py
|- response/llm_response.py

beacon/infra/
|- event_bus.py
|- mock_dispatcher.py
```

## Extension Points

- Add a new reaction by implementing the Reaction interface.
- Add a new inbound transport by adapting external payloads through EventAdapter.
- Replace dispatcher send_handler to integrate HTTP, queues, or internal workers.
- Use controls (hop/idempotency/rate) where your runtime policy requires safety gates.

## Release

Release process and tagging policy are documented in [docs/releasing.md](docs/releasing.md).

Local release gate:

```bash
ruff check beacon/ tests/ examples/
pytest -v
python -m build
```

Install from a release tag:

```bash
pip install "beacon @ git+https://github.com/nanacnote/beacon.git@v0.2.0"
```

## Running Tests

```bash
pytest tests/ -v
```

## License

MIT
