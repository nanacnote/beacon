"""
Mock Dispatcher: simulates LLM responses for testing.

Provides simple delay + echo behavior for development and testing
without needing a real LLM service.
"""

import asyncio

from beacon.core.llm_request import LLMRequest
from beacon.core.llm_response import LLMResponse


class MockDispatcher:
    """
    Mock LLM dispatcher for testing.

    Simulates LLM responses with:
    - Configurable delay (to simulate latency)
    - Echo behavior (returns request content)
    - Optional callback to handle responses
    """

    def __init__(
        self,
        delay_seconds: float = 0.1,
        response_callback=None,
    ):
        """
        Initialize MockDispatcher.

        Args:
            delay_seconds: Simulated latency before response
            response_callback: Async callable(response: LLMResponse) to handle responses
        """
        self._delay = delay_seconds
        self._response_callback = response_callback

    async def dispatch(self, request: LLMRequest) -> None:
        """
        Simulate LLM dispatch with delay.

        Args:
            request: LLMRequest to process
        """
        # Simulate latency
        await asyncio.sleep(self._delay)

        # Create mock response (echo user message)
        user_message = ""
        if request.messages:
            user_message = request.messages[0].get("content", "")

        response = LLMResponse(
            request_id=request.id,
            output={
                "content": f"Echo: {user_message}",
                "model": "mock-echo",
            },
            metadata={
                "correlation_id": request.conversation_id,
            },
        )

        # If callback provided, call it
        if self._response_callback:
            await self._response_callback(response)
