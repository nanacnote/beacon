# Implementation Plan: Reactive LLM Interface Layer

## Overview
Building a transport-agnostic, event-driven interface layer that ingests events (Matrix), transforms them to LLM requests, dispatches them, and re-injects responses. Python 3.11+, asyncio, abstract persistence, no response transport coupling.

## Phases & Steps

### Phase 1: Core Domain Models & Event Bus (Foundation)
**Duration estimate: 2-3 hours**
**No blockers**

1. Create `src/core/event.py` — Event class with id, type, source, timestamp, payload, metadata (hop_count, correlation_id)
2. Create `src/core/context.py` — Context class: conversation_id, actor_id, history, metadata, memory
3. Create `src/core/llm_request.py` — LLMRequest class: id, conversation_id, actor_id, messages, metadata, hints, tools (schemas only)
4. Create `src/core/llm_response.py` — LLMResponse class: request_id, output, metadata (input-only, for type hints)
5. Create `src/infra/event_bus.py` — EventBus class with async publish(), subscribe(), internal asyncio.Queue, worker pool support
6. Create `src/core/__init__.py` and `src/infra/__init__.py` with exports

**Verification:**
- All classes instantiate correctly
- EventBus can publish/subscribe without blocking
- Queue handles multiple concurrent publishes

---

### Phase 2: Reaction & Core Engine Logic (Business Logic)
**Duration estimate: 2-3 hours**
**Depends on Phase 1**

1. Create `src/core/reaction.py` — Reaction abstract class: triggers_on (list[str]), match(event) -> bool, async produce(event, ctx) -> list[LLMRequest]
2. Create `src/core/engine.py` — ReactionEngine class: async process(event, ctx) -> list[LLMRequest]; filters by triggers_on, runs all matches, aggregates outputs
3. Create `src/core/context_builder.py` — ContextBuilder class: async build(event) -> Context; creates context from event with conversation_id, actor_id, metadata (pluggable for history fetch)
4. Create `src/core/dispatcher.py` — Dispatcher class: async dispatch(request: LLMRequest); fire-and-forget, accepts abstract callback for response handling
5. Create `src/core/engine.py` (extend) — CoreEngine class: async handle_event(event); orchestrates build context → run reactions → dispatch

**Verification:**
- Reaction matching works for multiple event types
- CoreEngine processes event end-to-end without blocking
- Reactions can be composed/added dynamically

---

### Phase 3: Adapter Layer & Inbound (Matrix)
**Duration estimate: 2-3 hours**
**Depends on Phase 1 & 2**

1. Create `src/adapters/__init__.py`
2. Create `src/adapters/event_adapter.py` — EventAdapter class: from_external(raw_event) -> Event, to_external(action) -> dict
3. Create `src/adapters/inbound/__init__.py`
4. Create `src/adapters/inbound/matrix.py` — MatrixAdapter class: receives mautrix events, converts via EventAdapter, publishes to EventBus; multi-room support
5. Create `src/adapters/response/__init__.py`
6. Create `src/adapters/response/llm_response.py` — ResponseAdapter class: accepts LLM response (HTTP or queue), converts to Event(type="llm_response"), publishes to EventBus; consumer-facing callback

**Verification:**
- Matrix event → Event conversion preserves metadata
- Response → Event injection works
- Multi-room mapping correct

---

### Phase 4: Control Mechanisms (Safety)
**Duration estimate: 1-2 hours**
**Runs parallel with Phase 3, integrates into Phases 2-3**

1. Create `src/core/controls.py` — Control utilities:
   - HopCounter: check event.metadata["hop_count"] > MAX_HOPS (default 5)
   - IdempotencyTracker: in-memory or pluggable storage, track event_id + request_id
   - RateLimiter: per-conversation, per-actor, global limits (using asyncio.Semaphore)
2. Integrate into CoreEngine.handle_event() — check hop count, idempotency before processing
3. Integrate into Dispatcher — ensure request_id is set for correlation

**Verification:**
- Hop count blocks events > 5
- Duplicate requests rejected
- Rate limiting enforces limits

---

### Phase 5: Example Implementation & Testing Foundation
**Duration estimate: 2-3 hours**
**Depends on all prior phases**

1. Create `src/reactions/__init__.py`
2. Create `src/reactions/message_to_llm.py` — ConcreteMessageReaction(Reaction): triggers_on=["message"], match filters for valid messages, produce() creates LLMRequest from message content
3. Create `src/infra/mock_dispatcher.py` — MockDispatcher: simulates LLM with async delay + echo (for testing)
4. Create `tests/` directory structure:
   - `tests/test_event.py` — Event model tests
   - `tests/test_event_bus.py` — EventBus async publish/subscribe, worker pool
   - `tests/test_reaction_engine.py` — ReactionEngine filtering & aggregation
   - `tests/test_core_engine.py` — End-to-end event flow (no adapters)
   - `tests/test_controls.py` — Hop count, idempotency, rate limiting
   - `tests/conftest.py` — pytest async fixtures (event_loop, sample_event, etc.)
5. Create `examples/` directory:
   - `examples/single_room_flow.py` — Demo: Matrix event → LLMRequest → response loop

**Verification:**
- All tests pass with pytest
- Example flow runs end-to-end without errors
- Async fixtures work correctly

---

### Phase 6: Project Structure & Configuration
**Duration estimate: 1 hour**
**Parallel with Phase 1, blocks dependency resolution**

1. Create `pyproject.toml` — Python 3.11+, dependencies: pydantic, mautrix, pytest, pytest-asyncio
2. Create `src/__init__.py` (package root)
3. Create `.gitignore` (Python standard)
4. Create `README.md` — overview, quick start, architecture diagram reference to spec
5. Create `ARCHITECTURE.md` — link to spec, add any clarifications
6. Create `Makefile` or `scripts/` — common commands: test, lint, format

---

## Relevant Files (Critical Path)

**Core domain:**
- `src/core/event.py` — base Event model
- `src/core/reaction.py` — Reaction interface (critical for extensibility)
- `src/core/engine.py` — CoreEngine + ReactionEngine (orchestration heart)
- `src/core/context_builder.py` — pluggable context factory
- `src/core/controls.py` — hop count, idempotency, rate limiting

**Infrastructure:**
- `src/infra/event_bus.py` — queue-based async distribution
- `src/adapters/event_adapter.py` — event normalization (no transport leakage)

**Integration points:**
- `src/adapters/inbound/matrix.py` — mautrix entry point
- `src/adapters/response/llm_response.py` — consumer callback interface

**Testing:**
- `tests/test_core_engine.py` — validates full flow without adapters
- `tests/conftest.py` — async fixtures

---

## Verification Steps

### Unit Level
1. `pytest tests/test_event.py` — Event model serialization, id generation
2. `pytest tests/test_event_bus.py` — async publish, subscribe, queue draining
3. `pytest tests/test_reaction_engine.py` — reaction matching and aggregation

### Integration Level
1. `pytest tests/test_core_engine.py` — full event → context → reaction → dispatch flow
2. `pytest tests/test_controls.py` — hop count prevents loops, idempotency works

### Example Flow
1. Run `python examples/single_room_flow.py`
2. Verify: event published → reaction triggered → LLMRequest created → mock response re-injected → loop re-triggered

### Acceptance Criteria Met?
- ✓ Matrix message triggers Event
- ✓ Event produces LLMRequest via Reaction
- ✓ Request dispatched asynchronously
- ✓ Mock LLM response received
- ✓ Response converted to Event
- ✓ Event re-enters and triggers another Reaction

---

## Decisions & Constraints

- **Async Runtime**: asyncio (Python stdlib) — no third-party required
- **Context Persistence**: Abstract interface only — consumer implements storage (in-memory, SQLite, PostgreSQL, etc.)
- **Response Transport**: Not specified by library — consumer calls ResponseAdapter with whatever transport they use
- **Hop Count Limit**: Hardcoded to 5 (configurable in `src/core/controls.py`)
- **Idempotency Tracking**: In-memory by default (fine for MVP, upgradeable once storage is decided)
- **Rate Limiting**: Async semaphores (no external service needed)
- **Mock LLM**: Simple delay + echo for testing (replace with real dispatcher in production)

---

## Architecture Notes

- **No Transport Leakage**: EventAdapter ensures Matrix/mautrix details don't appear in Event
- **Fire-and-Forget Dispatch**: Dispatcher does NOT wait for response; ResponseAdapter injects response as separate event
- **Stateless Reactions**: All reactions are deterministic functions of (Event, Context)
- **Worker Pool**: EventBus internally manages workers consuming from async queue

---

## Key Decisions Table

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Async Runtime | asyncio | Stdlib, no external deps, good for 3.11+ |
| Context Persistence | Abstract/pluggable interface | Library stays storage-agnostic, consumer picks SQLite/PG/Redis |
| Response Transport | Not specified by library | Consumer calls ResponseAdapter; we don't enforce HTTP/queue |
| Rate Limiting Strategy | asyncio.Semaphore per-dimension | Lightweight, no external service |
| Hop Count Limit | 5 (configurable) | Prevents infinite loops safely |
| Idempotency | In-memory tracker (MVP) | Fast iteration; upgrade to persistent when storage decided |
| LLM Mock | Simple delay + echo | Minimal test harness, replace with real dispatcher in prod |

---

## Acceptance Criteria Verification

✅ Matrix message → Event (Phase 3)  
✅ Event → LLMRequest via Reaction (Phase 2)  
✅ Async dispatch without blocking (Phase 2)  
✅ Mock LLM response received (Phase 5)  
✅ Response → Event re-injection (Phase 3)  
✅ Event re-triggers reaction (Phase 5 integration test)
