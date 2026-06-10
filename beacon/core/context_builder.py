"""
Context Builder: creates Context from Event.

The ContextBuilder is a pluggable factory that extracts conversation and actor IDs
from events and optionally enriches with history/memory (consumer-provided).
"""

from typing import Any, Callable, Optional

from beacon.core.context import Context
from beacon.core.event import Event


class ContextBuilder:
    """
    Async context factory: Event → Context.

    Responsibilities:
    - Map event → (conversation_id, actor_id)
    - Optionally fetch history (consumer-provided callback)
    - Inject metadata (timestamp, environment, etc.)
    """

    def __init__(
        self,
        conversation_extractor: Optional[Callable[[Event], str]] = None,
        actor_extractor: Optional[Callable[[Event], str]] = None,
        history_fetcher: Optional[
            Callable[[str, str], Any]
        ] = None,  # async callable (conversation_id, actor_id) -> list
    ):
        """
        Initialize ContextBuilder with optional extraction functions.

        Args:
            conversation_extractor: Function to extract conversation_id from Event
            actor_extractor: Function to extract actor_id from Event
            history_fetcher: Async function to fetch history given (conversation_id, actor_id)
        """
        self._conversation_extractor = (
            conversation_extractor or self._default_conversation_extractor
        )
        self._actor_extractor = actor_extractor or self._default_actor_extractor
        self._history_fetcher = history_fetcher

    async def build(self, event: Event) -> Context:
        """
        Build a Context from an Event.

        Args:
            event: Source event

        Returns:
            Context: Fully initialized context
        """
        conversation_id = self._conversation_extractor(event)
        actor_id = self._actor_extractor(event)

        # Optionally fetch history
        history = []
        if self._history_fetcher:
            history = await self._history_fetcher(conversation_id, actor_id)

        return Context(
            conversation_id=conversation_id,
            actor_id=actor_id,
            history=history,
            metadata={},
            memory={},
        )

    @staticmethod
    def _default_conversation_extractor(event: Event) -> str:
        """
        Default: extract conversation_id from event payload.

        Args:
            event: Source event

        Returns:
            str: conversation_id or empty string if not found
        """
        return event.payload.get("room") or event.payload.get("channel") or ""

    @staticmethod
    def _default_actor_extractor(event: Event) -> str:
        """
        Default: extract actor_id from event payload.

        Args:
            event: Source event

        Returns:
            str: actor_id or empty string if not found
        """
        return event.payload.get("sender") or event.payload.get("user") or ""
