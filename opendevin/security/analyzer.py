from opendevin.core.logger import opendevin_logger as logger
from opendevin.events.action.action import Action, ActionSecurityRisk
from opendevin.events.event import Event
from opendevin.events.stream import EventStream, EventStreamSubscriber


class SecurityAnalyzer:
    """Security analyzer that receives all events and analyzes agent actions for security risks."""

    def __init__(self, event_stream: EventStream):
        """Initializes a new instance of the SecurityAnalyzer class.

        Args:
            event_stream: The event stream to listen for events.
        """
        self.event_stream = event_stream
        self.event_stream.subscribe(
            EventStreamSubscriber.SECURITY_ANALYZER, self.on_event
        )

    async def on_event(self, event: Event) -> None:
        """Handles the incoming event, and when Action is received, analyzes it for security risks."""
        logger.info(f'SecurityAnalyzer received event: {event}')
        if not isinstance(event, Action):
            await self.log_event(event)
            return
        event.security_risk = await self.security_risk(event)  # type: ignore [attr-defined]
        await self.log_event(event)

    async def log_event(self, event: Event) -> None:
        """Logs the incoming event."""
        pass

    async def security_risk(self, event: Action) -> ActionSecurityRisk:
        """Evaluates the Action for security risks and returns the risk level."""
        raise NotImplementedError(
            'Need to implement security_risk method in SecurityAnalyzer subclass'
        )
