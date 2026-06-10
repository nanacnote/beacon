"""
Reaction Engine & Core Engine: orchestration heart.

ReactionEngine filters and runs reactions, aggregating their outputs.
CoreEngine coordinates the full flow: context → reactions → dispatch.
"""

from beacon.core.context import Context
from beacon.core.context_builder import ContextBuilder
from beacon.core.dispatcher import Dispatcher
from beacon.core.event import Event
from beacon.core.llm_request import LLMRequest
from beacon.core.reaction import Reaction


class ReactionEngine:
    """
    Filters and executes reactions for a given event.

    Responsibilities:
    - Filter reactions by triggers_on
    - Execute all matching reactions
    - Aggregate LLMRequests
    """

    def __init__(self, reactions: list[Reaction]):
        """
        Initialize with a set of reactions.

        Args:
            reactions: List of Reaction instances to consider
        """
        self._reactions = reactions

    async def process(
        self, event: Event, ctx: Context
    ) -> list[LLMRequest]:
        """
        Process an event through all matching reactions.

        Args:
            event: Event to process
            ctx: Context for processing

        Returns:
            list[LLMRequest]: Aggregated requests from all reactions
        """
        requests: list[LLMRequest] = []

        for reaction in self._reactions:
            # Filter by triggers_on
            if event.type not in reaction.triggers_on:
                continue

            # Check match condition
            if not reaction.match(event):
                continue

            # Run reaction and collect requests
            reaction_requests = await reaction.produce(event, ctx)
            requests.extend(reaction_requests)

        return requests


class CoreEngine:
    """
    Main orchestrator: Event → Context → Reactions → Dispatch.

    Coordinates the full flow without blocking.
    """

    def __init__(
        self,
        reaction_engine: ReactionEngine,
        context_builder: ContextBuilder,
        dispatcher: Dispatcher,
    ):
        """
        Initialize CoreEngine with dependencies.

        Args:
            reaction_engine: ReactionEngine for producing requests
            context_builder: ContextBuilder for creating context
            dispatcher: Dispatcher for sending requests
        """
        self._reaction_engine = reaction_engine
        self._context_builder = context_builder
        self._dispatcher = dispatcher

    async def handle_event(self, event: Event) -> None:
        """
        End-to-end event processing: context → reactions → dispatch.

        Args:
            event: Event to process
        """
        # Build context
        ctx = await self._context_builder.build(event)

        # Run reactions
        requests = await self._reaction_engine.process(event, ctx)

        # Dispatch all requests (fire-and-forget)
        for request in requests:
            await self._dispatcher.dispatch(request)
