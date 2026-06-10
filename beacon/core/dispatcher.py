"""
Dispatcher: fire-and-forget async LLMRequest dispatch.

The Dispatcher transforms LLMRequests for an external LLM system.
It does NOT wait for responses; ResponseAdapter handles response re-injection.
"""

import logging
from inspect import isawaitable
from typing import Any, Callable, Optional

from beacon.core.llm_request import LLMRequest

logger = logging.getLogger(__name__)


class Dispatcher:
    """
    Fire-and-forget dispatcher for LLMRequests.

    Takes an async callback that the consumer provides to handle response
    (HTTP POST, queue publish, etc.). Dispatcher itself remains transport-agnostic.
    """

    def __init__(
        self,
        send_handler: Optional[
            Callable[[LLMRequest], Any]
        ] = None,
    ):
        """
        Initialize Dispatcher with optional send handler.

        Args:
            send_handler: Async callable(request: LLMRequest) that handles dispatch.
                         If None, dispatch becomes a no-op (for testing).
        """
        self._send_handler = send_handler

    async def dispatch(self, request: LLMRequest) -> None:
        """
        Dispatch an LLMRequest asynchronously (fire-and-forget).

        Args:
            request: LLMRequest to dispatch
        """
        if self._send_handler:
            try:
                result = self._send_handler(request)
                if isawaitable(result):
                    await result
            except Exception:
                logger.exception("Dispatcher send_handler failed for request_id=%s", request.id)
                raise
        else:
            logger.debug("Dispatcher no-op for request_id=%s", request.id)
