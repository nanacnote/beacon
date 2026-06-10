"""
Concrete reactions: real business logic implementations.
"""

from beacon.core.context import Context
from beacon.core.event import Event
from beacon.core.llm_request import LLMRequest
from beacon.core.reaction import Reaction


class MessageToLLMReaction(Reaction):
    """
    Simple, concrete reaction: message event → LLMRequest.

    Converts incoming message events to LLM requests,
    enabling the core loop to function.
    """

    @property
    def triggers_on(self) -> list[str]:
        """Listen for message events."""
        return ["message"]

    def match(self, event: Event) -> bool:
        """Match if event has message text."""
        return "text" in event.payload and event.payload.get("text", "").strip()

    async def produce(self, event: Event, ctx: Context) -> list[LLMRequest]:
        """Convert message to LLMRequest."""
        text = event.payload["text"]

        request = LLMRequest(
            conversation_id=ctx.conversation_id,
            actor_id=ctx.actor_id,
            messages=[{"role": "user", "content": text}],
            metadata={"source_event_id": event.id},
            hints={"be_concise": True},
        )

        return [request]
