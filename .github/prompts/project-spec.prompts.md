# SYSTEM SPECIFICATION: Reactive LLM Interface Layer (Transport-Agnostic)

## 1. PURPOSE

Design and implement a **transport-agnostic, event-driven interface layer** that:

* Ingests events from external messaging systems (initially Matrix via mautrix)
* Transforms those events into structured **LLM requests**
* Dispatches requests to a downstream LLM system (out of scope)
* Receives LLM responses and re-injects them as events
* Applies a **reaction-based transformation model** across all events

This system does **NOT**:

* Execute tools
* Interpret or enforce LLM decisions
* Perform agent orchestration
* Depend on any specific LLM provider

---

## 2. CORE DESIGN PRINCIPLES

1. **Transport Agnostic**

   * No core logic may depend on Matrix, mautrix, or any external SDK

2. **Event-Driven Architecture**

   * All inputs and outputs are normalized as events
   * No synchronous/blocking flows

3. **Separation of Concerns**

   * Adapters handle IO
   * Core handles transformation
   * Downstream handles intelligence

4. **Stateless Core Logic**

   * Core components must not hold mutable runtime state

5. **Async First**

   * Entire system must be non-blocking and asyncio-native

6. **Composable Reactions**

   * Logic is expressed as independent, pluggable reaction units

---

## 3. HIGH-LEVEL ARCHITECTURE

```
Inbound Adapter (Matrix via mautrix)
        ↓
Event Adapter (normalize)
        ↓
Event Bus (async queue + workers)
        ↓
Reaction Engine
        ↓
Context Builder
        ↓
LLM Request Builder
        ↓
Dispatcher → External LLM System
        ↓
Response Adapter (HTTP/Queue)
        ↓
Event Adapter
        ↓
Event Bus (loop)
```

---

## 4. CORE DOMAIN MODELS

### 4.1 Event

```python
class Event:
    id: str
    type: str  # "message", "timer", "llm_response", etc.
    source: str  # abstract source (not transport-specific)
    timestamp: datetime

    payload: dict
    metadata: dict  # includes hop_count, correlation_id, etc.
```

---

### 4.2 Context

```python
class Context:
    conversation_id: str
    actor_id: str

    history: list
    metadata: dict
    memory: dict  # optional
```

---

### 4.3 LLMRequest

```python
class LLMRequest:
    id: str
    conversation_id: str
    actor_id: str

    messages: list
    metadata: dict
    hints: dict

    tools: list  # schemas only, not execution
```

---

### 4.4 LLMResponse (Input Only)

```python
class LLMResponse:
    request_id: str
    output: dict
    metadata: dict
```

---

## 5. CORE COMPONENTS

---

### 5.1 Event Bus

#### Requirements:

* Async
* Queue-based
* Multi-consumer
* Non-blocking

#### Interface:

```python
class EventBus:
    async def publish(event: Event): ...
    def subscribe(handler): ...
```

#### Behavior:

* Must use internal queue
* Must support worker pool
* Must not block producers

---

### 5.2 Reaction

#### Definition:

```python
class Reaction:
    triggers_on: list[str]

    def match(self, event: Event) -> bool: ...
    async def produce(self, event: Event, ctx: Context) -> list[LLMRequest]: ...
```

#### Rules:

* Must be pure (no side effects)
* Must not call external systems
* Must not depend on transport layer

---

### 5.3 Reaction Engine

```python
class ReactionEngine:
    async def process(event: Event, ctx: Context) -> list[LLMRequest]
```

#### Behavior:

* Filter reactions by `triggers_on`
* Execute all matching reactions
* Aggregate outputs

---

### 5.4 Context Builder

```python
class ContextBuilder:
    async def build(event: Event) -> Context
```

#### Responsibilities:

* Map event → conversation_id, actor_id
* Fetch recent history (if implemented)
* Inject metadata (time, environment, etc.)

---

### 5.5 Dispatcher

```python
class Dispatcher:
    async def dispatch(request: LLMRequest)
```

#### Requirements:

* Fire-and-forget
* No waiting for response
* Supports HTTP / queue / Kafka

---

### 5.6 Core Engine

```python
class CoreEngine:
    async def handle_event(event: Event)
```

#### Flow:

1. Build context
2. Run reaction engine
3. Dispatch all LLMRequests

---

## 6. ADAPTER LAYER

---

### 6.1 Inbound Adapter (Matrix via mautrix)

Responsibilities:

* Receive Matrix events
* Convert to internal Event via EventAdapter
* Publish to EventBus

Constraints:

* No business logic allowed

---

### 6.2 Event Adapter

```python
class EventAdapter:
    def from_external(raw_event) -> Event
    def to_external(action) -> external_format
```

---

### 6.3 Response Adapter

Responsibilities:

* Accept LLM responses (HTTP or queue)
* Convert to Event(type="llm_response")
* Publish to EventBus

---

## 7. CONTROL MECHANISMS (MANDATORY)

---

### 7.1 Hop Count

Prevent infinite loops:

```python
if event.metadata["hop_count"] > MAX_HOPS:
    discard
```

---

### 7.2 Idempotency

Track:

* event_id
* request_id

Avoid duplicate processing

---

### 7.3 Rate Limiting

Must support:

* per conversation
* per actor
* global

---

### 7.4 Filtering

Reactions must be able to:

* ignore irrelevant events
* reduce LLM load

---

## 8. NON-FUNCTIONAL REQUIREMENTS

---

### Scalability

* Must support horizontal scaling
* Stateless workers preferred

---

### Observability

* Log every event
* Log every LLMRequest
* Correlate request_id ↔ event_id

---

### Fault Tolerance

* EventBus must handle spikes
* Dispatcher failures must not crash system

---

### Extensibility

* Must support adding new adapters without core changes
* Must support adding new reactions dynamically

---

## 9. DIRECTORY STRUCTURE

```
core/
  event.py
  context.py
  reaction.py
  engine.py
  llm_request.py

adapters/
  inbound/
    matrix.py
  outbound/
    dispatcher.py
  response/
    llm_response.py

infra/
  event_bus.py
  queue.py

app/
  main.py
```

---

## 10. EXPLICIT NON-GOALS

* No tool execution
* No prompt engineering embedded in core
* No LLM provider logic
* No synchronous request/response loops
* No transport leakage into core domain

---

## 11. ACCEPTANCE CRITERIA

The system is complete when:

1. A Matrix message triggers an Event
2. Event produces an LLMRequest via Reaction
3. Request is dispatched asynchronously
4. A mocked LLM response is received
5. Response is converted to Event
6. Event re-enters system and triggers another Reaction

---

## 12. IMPLEMENTATION PRIORITY

1. Event + EventBus
2. CoreEngine + ReactionEngine
3. One Reaction (message → LLMRequest)
4. Dispatcher (mock)
5. Matrix Adapter (mautrix)
6. Response Adapter

---

## FINAL INSTRUCTION

Follow this specification strictly.

Do not introduce:

* blocking calls
* tight coupling to external systems
* agent-like abstractions

Focus on:

* correctness
* composability
* clean boundaries
* long-term extensibility
