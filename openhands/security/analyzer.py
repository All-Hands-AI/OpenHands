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

        def sync_on_event(event: Event) -> None:
            asyncio.create_task(self.on_event(event))

        self.event_stream.subscribe(
            EventStreamSubscriber.SECURITY_ANALYZER, sync_on_event, str(uuid4())
        )

    async def on_event(self, event: Event) -> None:
        """Handles the incoming event, and when Action is received, analyzes it for security risks."""
        logger.debug(f'SecurityAnalyzer received event: {event}')
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
