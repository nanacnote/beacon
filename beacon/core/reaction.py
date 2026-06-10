"""
Reaction interface: the core business logic abstraction.

A Reaction is a pure, stateless function that matches events and produces LLMRequests.
Reactions are composable, extensible, and have no side effects.
"""

from abc import ABC, abstractmethod

from beacon.core.context import Context
from beacon.core.event import Event
from beacon.core.llm_request import LLMRequest


class Reaction(ABC):
    """
    Abstract base for event → LLMRequest transformations.

    A Reaction defines:
    1. Which events it cares about (triggers_on)
    2. Whether a specific event matches (match)
    3. How to transform that event into zero or more LLMRequests (produce)

    Reactions must be pure (no side effects) and stateless.
    """

    @property
    @abstractmethod
    def triggers_on(self) -> list[str]:
        """
        Event types this reaction listens for.

        Returns:
            list[str]: Event type names (e.g., ["message", "timer"])
        """
        pass

    @abstractmethod
    def match(self, event: Event) -> bool:
        """
        Determine if this reaction should process the event.

        Args:
            event: Event to evaluate

        Returns:
            bool: True if this reaction should produce() for this event
        """
        pass

    @abstractmethod
    async def produce(
        self, event: Event, ctx: Context
    ) -> list[LLMRequest]:
        """
        Transform an event (and context) into zero or more LLMRequests.

        Args:
            event: The triggering event
            ctx: Context for this request

        Returns:
            list[LLMRequest]: Requests to dispatch (may be empty)
        """
        pass
