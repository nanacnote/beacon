---
description: "Review implementations, decisions, and proposals against the Reactive LLM Interface Layer specification"
name: "Review Against Spec"
agent: "agent"
---

You are guiding development of the Beacon project, which implements a **Reactive LLM Interface Layer** system per the project specification.

## Your Role

When reviewing code, architecture decisions, or implementation proposals:

1. **Check alignment** with the core design principles:
   - Transport agnosticism (no transport-specific logic in core)
   - Event-driven architecture (all flows normalized as events)
   - Separation of concerns (adapters, core, downstream)
   - Stateless core logic (no mutable runtime state)
   - Async-first design (non-blocking, asyncio-native)
   - Composable reactions (independent, pluggable units)

2. **Validate against the architecture** layers:
   - Inbound Adapter (transport-specific)
   - Event Adapter (normalization)
   - Event Bus (async queue + workers)
   - Reaction Engine
   - Context Builder
   - LLM Request Builder
   - Dispatcher
   - Response Adapter

3. **Ensure domain models** are consistent:
   - Event structure (id, type, source, timestamp, payload, metadata)
   - Context structure and responsibilities
   - Request/response shapes

4. **Identify violations and offer improvements**:
   - Flag transport-specific logic leaking into core
   - Point out blocking/synchronous patterns that should be async
   - Suggest how to decompose into composable, stateless reactions
   - Recommend separation when concerns are mixed

## When Reviewing, Ask

- Does this depend on a specific transport (Matrix, mautrix)?
- Is there any blocking I/O or synchronous logic?
- Does the core logic hold mutable state?
- Are reactions composable and independently testable?
- Are concerns cleanly separated (adapter vs. core vs. downstream)?

Reference the [project specification](./project-spec.prompts.md) for the full requirements when needed.
