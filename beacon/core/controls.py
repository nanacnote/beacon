"""
Control mechanisms: hop count, idempotency, and rate limiting.

These components prevent infinite loops, duplicate processing, and abuse.
"""

import asyncio
from typing import Dict, Tuple


class HopCounter:
    """
    Prevent infinite loops by tracking event hops.

    An event's hop_count increments each time it enters the system.
    When it exceeds MAX_HOPS, the event is discarded.
    """

    MAX_HOPS = 5

    @staticmethod
    def is_too_many_hops(hop_count: int, max_hops: int = MAX_HOPS) -> bool:
        """
        Check if hop count exceeds the limit.

        Args:
            hop_count: Current hop count
            max_hops: Maximum allowed hops

        Returns:
            bool: True if hop_count > max_hops
        """
        return hop_count > max_hops

    @staticmethod
    def increment(hop_count: int) -> int:
        """
        Increment hop count.

        Args:
            hop_count: Current hop count

        Returns:
            int: hop_count + 1
        """
        return hop_count + 1


class IdempotencyTracker:
    """
    Track event and request IDs to prevent duplicate processing.

    In-memory storage suitable for MVP. Can be replaced with
    persistent storage (Redis, database) by consumer.
    """

    def __init__(self) -> None:
        """Initialize in-memory tracker."""
        self._seen_event_ids: set[str] = set()
        self._seen_request_ids: set[str] = set()

    def has_seen_event(self, event_id: str) -> bool:
        """
        Check if event has been seen before.

        Args:
            event_id: Event ID to check

        Returns:
            bool: True if already seen
        """
        return event_id in self._seen_event_ids

    def mark_event_seen(self, event_id: str) -> None:
        """
        Mark an event as seen.

        Args:
            event_id: Event ID to mark
        """
        self._seen_event_ids.add(event_id)

    def has_seen_request(self, request_id: str) -> bool:
        """
        Check if request has been seen before.

        Args:
            request_id: Request ID to check

        Returns:
            bool: True if already seen
        """
        return request_id in self._seen_request_ids

    def mark_request_seen(self, request_id: str) -> None:
        """
        Mark a request as seen.

        Args:
            request_id: Request ID to mark
        """
        self._seen_request_ids.add(request_id)


class RateLimiter:
    """
    Rate limiting with per-conversation, per-actor, and global limits.

    Uses asyncio.Semaphore for lightweight, async-native limiting.
    """

    def __init__(
        self,
        global_limit: int = 100,
        per_conversation_limit: int = 10,
        per_actor_limit: int = 20,
    ):
        """
        Initialize RateLimiter with configurable limits.

        Args:
            global_limit: Max concurrent requests globally
            per_conversation_limit: Max concurrent requests per conversation
            per_actor_limit: Max concurrent requests per actor
        """
        self._global_semaphore = asyncio.Semaphore(global_limit)
        self._per_conversation_limit = per_conversation_limit
        self._per_actor_limit = per_actor_limit
        self._conversation_semaphores: Dict[str, asyncio.Semaphore] = {}
        self._actor_semaphores: Dict[str, asyncio.Semaphore] = {}

    async def acquire(
        self, conversation_id: str, actor_id: str
    ) -> Tuple[asyncio.Semaphore, asyncio.Semaphore, asyncio.Semaphore]:
        """
        Acquire rate limit permits for all dimensions.

        Args:
            conversation_id: Conversation ID for per-conversation limiting
            actor_id: Actor ID for per-actor limiting

        Returns:
            Tuple[Semaphore, Semaphore, Semaphore]: Global, conversation, actor semaphores
                (for use with async context managers)

        Raises:
            asyncio.TimeoutError: If cannot acquire within timeout (not used here)
        """
        # Global
        await self._global_semaphore.acquire()

        # Per-conversation
        if conversation_id not in self._conversation_semaphores:
            self._conversation_semaphores[conversation_id] = asyncio.Semaphore(
                self._per_conversation_limit
            )
        await self._conversation_semaphores[conversation_id].acquire()

        # Per-actor
        if actor_id not in self._actor_semaphores:
            self._actor_semaphores[actor_id] = asyncio.Semaphore(
                self._per_actor_limit
            )
        await self._actor_semaphores[actor_id].acquire()

        return (
            self._global_semaphore,
            self._conversation_semaphores[conversation_id],
            self._actor_semaphores[actor_id],
        )

    def release(
        self,
        global_sem: asyncio.Semaphore,
        conversation_sem: asyncio.Semaphore,
        actor_sem: asyncio.Semaphore,
    ) -> None:
        """
        Release all acquired semaphores.

        Args:
            global_sem: Global semaphore to release
            conversation_sem: Conversation semaphore to release
            actor_sem: Actor semaphore to release
        """
        global_sem.release()
        conversation_sem.release()
        actor_sem.release()
