from typing import Any

from fastapi import Request

from openhands.events.action.action import (
    Action,
    ActionConfirmationStatus,
    ActionSecurityRisk,
)
from openhands.events.event import Event
from openhands.events.stream import EventStream
from openhands.security.analyzer import SecurityAnalyzer


class BullySecurityAnalyzer(SecurityAnalyzer):
    """A security analyzer that blocks all actions by marking them as high risk."""

    settings: dict[str, Any] = {}

    def __init__(self, event_stream: EventStream) -> None:
        """Initializes a new instance of the BullySecurityAnalyzer class.

        Args:
            event_stream: The event stream to listen for events.
        """
        super().__init__(event_stream)
        self.settings = {}

    async def handle_api_request(self, request: Request) -> Any:
        """Handles the incoming API request."""
        raise NotImplementedError('API requests not supported in BullySecurityAnalyzer')

    async def security_risk(self, event: Action) -> ActionSecurityRisk:
        """Evaluates the Action for security risks and returns the risk level.

        Always returns HIGH risk for all actions.
        """
        return ActionSecurityRisk.HIGH

    async def should_confirm(self, event: Event) -> bool:
        """Determines if the event should be confirmed based on its security risk.

        Args:
            event: The event to check.

        Returns:
            True if the event should be confirmed, False otherwise.
        """
        risk = event.security_risk if hasattr(event, 'security_risk') else None  # type: ignore [attr-defined]
        return (
            risk is not None
            and risk < self.settings.get('RISK_SEVERITY', ActionSecurityRisk.MEDIUM)
            and hasattr(event, 'confirmation_state')
            and event.confirmation_state
            == ActionConfirmationStatus.AWAITING_CONFIRMATION
        )
