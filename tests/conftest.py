"""
Pytest configuration and shared async fixtures for Beacon tests.
"""

import pytest

from beacon.core import Context, Event, LLMRequest


@pytest.fixture
def sample_event() -> Event:
    """
    Fixture: sample message event for testing.

    Returns:
        Event: A basic message event with default metadata
    """
    return Event(
        type="message",
        source="matrix",
        payload={
            "text": "Hello, world!",
            "sender": "user:example.com",
            "room": "!room:example.com",
        },
        metadata={"hop_count": 0, "correlation_id": "test-corr-id"},
    )


@pytest.fixture
def sample_context() -> Context:
    """
    Fixture: sample context for testing.

    Returns:
        Context: A basic context with conversation and actor IDs
    """
    return Context(
        conversation_id="!room:example.com",
        actor_id="user:example.com",
        history=[],
        metadata={},
        memory={},
    )


@pytest.fixture
def sample_llm_request() -> LLMRequest:
    """
    Fixture: sample LLMRequest for testing.

    Returns:
        LLMRequest: A basic request with sample messages
    """
    return LLMRequest(
        conversation_id="!room:example.com",
        actor_id="user:example.com",
        messages=[{"role": "user", "content": "Hello, world!"}],
        metadata={},
        hints={},
        tools=[],
    )
