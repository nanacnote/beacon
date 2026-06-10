"""
Event Bus: async queue-based event distribution with worker pool.

The EventBus is the central nervous system: it accepts published events,
queues them, and distributes them to all subscribed handlers asynchronously.
"""

import asyncio
import logging
from collections import defaultdict
from typing import Callable, Coroutine

from beacon.core.event import Event

logger = logging.getLogger(__name__)


class EventBus:
    """
    Async, queue-based event publisher/subscriber.

    Features:
    - Non-blocking publish (enqueues and returns)
    - Multiple independent handlers per event type
    - Internal worker pool consuming from asyncio.Queue
    - No synchronous/blocking flows
    """

    def __init__(self, max_workers: int = 10, queue_size: int = 1000):
        """
        Initialize the EventBus.

        Args:
            max_workers: Number of concurrent workers processing events
            queue_size: Maximum size of internal event queue
        """
        self._queue: asyncio.Queue[Event] = asyncio.Queue(maxsize=queue_size)
        self._handlers: dict[str, list[Callable[[Event], Coroutine]]] = defaultdict(list)
        self._max_workers = max_workers
        self._workers: list[asyncio.Task] = []
        self._running = False

    async def start(self) -> None:
        """Start worker pool to consume events from queue."""
        if self._running:
            return
        self._running = True
        for worker_index in range(self._max_workers):
            worker = asyncio.create_task(
                self._worker_loop(),
                name=f"event-bus-worker-{worker_index}",
            )
            self._workers.append(worker)

    async def stop(self, timeout: float = 5.0) -> None:
        """Stop workers and drain queue within a bounded timeout."""
        self._running = False
        if self._workers:
            await asyncio.gather(*self._workers, return_exceptions=True)
        self._workers.clear()

    async def publish(self, event: Event) -> None:
        """
        Publish an event (non-blocking enqueue).

        Args:
            event: Event to publish

        Raises:
            asyncio.QueueFull: If internal queue is at max capacity
        """
        self._queue.put_nowait(event)

    def subscribe(
        self, event_type: str, handler: Callable[[Event], Coroutine]
    ) -> None:
        """
        Subscribe a handler to events of a given type.

        Args:
            event_type: Event type to listen for (or "*" for all)
            handler: Async callable that receives Event
        """
        self._handlers[event_type].append(handler)

    async def _worker_loop(self) -> None:
        """
        Internal worker loop: consume events and dispatch to handlers.
        Runs concurrently with other workers.
        """
        while self._running or not self._queue.empty():
            try:
                event = await asyncio.wait_for(self._queue.get(), timeout=0.5)
            except asyncio.TimeoutError:
                continue

            try:
                await self._dispatch(event)
            except Exception:
                logger.exception(
                    "Unhandled event dispatch failure for type=%s id=%s",
                    event.type,
                    event.id,
                )
            finally:
                self._queue.task_done()

    async def _dispatch(self, event: Event) -> None:
        """
        Dispatch event to all subscribed handlers for this type.

        Args:
            event: Event to dispatch
        """
        # Collect all matching handler coroutines
        tasks = []

        # Type-specific handlers
        if event.type in self._handlers:
            for handler in self._handlers[event.type]:
                tasks.append(handler(event))

        # Wildcard handlers
        if "*" in self._handlers:
            for handler in self._handlers["*"]:
                tasks.append(handler(event))

        # Run all handlers concurrently and log failures for observability.
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for result in results:
                if isinstance(result, Exception):
                    logger.error(
                        "Event handler failed for event type=%s id=%s: %s",
                        event.type,
                        event.id,
                        result,
                    )
