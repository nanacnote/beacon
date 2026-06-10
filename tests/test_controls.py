"""Tests for control mechanisms: hop count, idempotency, rate limiting."""

import pytest

from beacon.core.controls import HopCounter, IdempotencyTracker, RateLimiter


class TestHopCounter:
    """Tests for HopCounter."""

    def test_hop_counter_within_limit(self) -> None:
        """Test that hop counts within limit are accepted."""
        assert not HopCounter.is_too_many_hops(0)
        assert not HopCounter.is_too_many_hops(3)
        assert not HopCounter.is_too_many_hops(5)

    def test_hop_counter_exceeds_limit(self) -> None:
        """Test that hop counts exceeding limit are rejected."""
        assert HopCounter.is_too_many_hops(6)
        assert HopCounter.is_too_many_hops(10)

    def test_hop_counter_increment(self) -> None:
        """Test hop count incrementing."""
        assert HopCounter.increment(0) == 1
        assert HopCounter.increment(4) == 5
        assert HopCounter.increment(5) == 6


class TestIdempotencyTracker:
    """Tests for IdempotencyTracker."""

    def test_tracker_marks_event_as_seen(self) -> None:
        """Test marking events as seen."""
        tracker = IdempotencyTracker()

        event_id = "event-123"

        assert not tracker.has_seen_event(event_id)
        tracker.mark_event_seen(event_id)
        assert tracker.has_seen_event(event_id)

    def test_tracker_multiple_events(self) -> None:
        """Test tracking multiple distinct events."""
        tracker = IdempotencyTracker()

        tracker.mark_event_seen("event-1")
        tracker.mark_event_seen("event-2")
        tracker.mark_event_seen("event-3")

        assert tracker.has_seen_event("event-1")
        assert tracker.has_seen_event("event-2")
        assert tracker.has_seen_event("event-3")
        assert not tracker.has_seen_event("event-4")

    def test_tracker_separate_event_and_request_tracking(self) -> None:
        """Test that event and request IDs are tracked separately."""
        tracker = IdempotencyTracker()

        # Same ID used for both event and request
        same_id = "id-123"

        tracker.mark_event_seen(same_id)
        assert tracker.has_seen_event(same_id)
        assert not tracker.has_seen_request(same_id)

        tracker.mark_request_seen(same_id)
        assert tracker.has_seen_request(same_id)


class TestRateLimiter:
    """Tests for RateLimiter."""

    @pytest.mark.asyncio
    async def test_rate_limiter_acquire_release(self) -> None:
        """Test basic acquire/release."""
        limiter = RateLimiter()

        global_sem, conv_sem, actor_sem = await limiter.acquire("conv-1", "actor-1")

        # Semaphores should be acquired (count decreased)
        assert global_sem._value < 100  # Global default is 100
        assert conv_sem._value < 10  # Per-conversation default is 10
        assert actor_sem._value < 20  # Per-actor default is 20

        limiter.release(global_sem, conv_sem, actor_sem)

        # After release, values should be back to original
        assert global_sem._value == 100
        assert conv_sem._value == 10
        assert actor_sem._value == 20

    @pytest.mark.asyncio
    async def test_rate_limiter_per_conversation(self) -> None:
        """Test per-conversation limiting."""
        limiter = RateLimiter(per_conversation_limit=2)

        # Acquire for conversation 1
        g1, c1, a1 = await limiter.acquire("conv-1", "actor-1")
        assert c1._value == 1  # One acquired

        g2, c2, a2 = await limiter.acquire("conv-1", "actor-2")
        assert c2 is c1  # Same semaphore for same conversation
        assert c2._value == 0  # Two acquired (limit reached)

        # Release
        limiter.release(g1, c1, a1)
        assert c1._value == 1

        # Different conversation should have its own semaphore
        g3, c3, a3 = await limiter.acquire("conv-2", "actor-1")
        assert c3 is not c1
        assert c3._value == 1

        # Cleanup
        limiter.release(g2, c2, a2)
        limiter.release(g3, c3, a3)

    @pytest.mark.asyncio
    async def test_rate_limiter_per_actor(self) -> None:
        """Test per-actor limiting."""
        limiter = RateLimiter(per_actor_limit=2)

        # Acquire for actor 1
        g1, c1, a1 = await limiter.acquire("conv-1", "actor-1")
        g2, c2, a2 = await limiter.acquire("conv-2", "actor-1")

        # Different conversations, same actor
        assert a2 is a1  # Same actor semaphore
        assert a1._value == 0  # Both permits used

        # Cleanup
        limiter.release(g1, c1, a1)
        limiter.release(g2, c2, a2)
