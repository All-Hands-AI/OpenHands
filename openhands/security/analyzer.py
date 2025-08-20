import asyncio
from typing import Any
from uuid import uuid4

from fastapi import Request

from openhands.core.logger import openhands_logger as logger
from openhands.events.action.action import Action, ActionSecurityRisk
from openhands.events.event import Event
from openhands.events.stream import EventStream, EventStreamSubscriber


class SecurityAnalyzer:
    """Security analyzer that receives all events and analyzes agent actions for security risks."""

    def __init__(self, event_stream: EventStream) -> None:
        """Initializes a new instance of the SecurityAnalyzer class.

        Args:
            event_stream: The event stream to listen for events.
        """
        self.event_stream = event_stream
        # Track processed event IDs to avoid double-processing when on_event is invoked
        # both via EventStream subscription and directly (e.g., in tests)
        self._processed_event_ids: set[int] = set()

        def sync_on_event(event: Event) -> None:
            """Bridge EventStream thread callbacks to asyncio.

            In production, EventStream processes callbacks on dedicated worker threads
            without a running asyncio loop. Creating a new loop per callback is too
            heavy and can swallow exceptions. Here we try to schedule on an existing
            loop when available, otherwise run the coroutine synchronously.
            """
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(self.on_event(event))
            except RuntimeError:
                # No running loop in this thread; execute synchronously
                asyncio.run(self.on_event(event))

        self.event_stream.subscribe(
            EventStreamSubscriber.SECURITY_ANALYZER, sync_on_event, str(uuid4())
        )

    async def on_event(self, event: Event) -> None:
        """Handles the incoming event, and when Action is received, analyzes it for security risks.

        Ensures idempotency: the same event (by ID) is only analyzed once.
        """
        logger.debug(f'SecurityAnalyzer received event: {event}')
        # If the event has already been processed, skip to avoid duplicates
        if event.id != Event.INVALID_ID and event.id in self._processed_event_ids:
            return
        # Mark as processed early to avoid races; safe since analysis is read-only
        if event.id != Event.INVALID_ID:
            self._processed_event_ids.add(event.id)

        await self.log_event(event)
        if not isinstance(event, Action):
            return

        try:
            # Set the security_risk attribute on the event
            event.security_risk = await self.security_risk(event)  # type: ignore [attr-defined]
            await self.act(event)
        except Exception as e:
            logger.error(f'Error occurred while analyzing the event: {e}')

    async def handle_api_request(self, request: Request) -> Any:
        """Handles the incoming API request."""
        raise NotImplementedError(
            'Need to implement handle_api_request method in SecurityAnalyzer subclass'
        )

    async def log_event(self, event: Event) -> None:
        """Logs the incoming event."""
        pass

    async def act(self, event: Event) -> None:
        """Performs an action based on the analyzed event."""
        pass

    async def security_risk(self, event: Action) -> ActionSecurityRisk:
        """Evaluates the Action for security risks and returns the risk level."""
        raise NotImplementedError(
            'Need to implement security_risk method in SecurityAnalyzer subclass'
        )

    async def close(self) -> None:
        """Cleanup resources allocated by the SecurityAnalyzer."""
        pass
