"""Security analyzer that uses LLM-provided risk assessments."""

from typing import Any

from fastapi import Request

from openhands.core.logger import openhands_logger as logger
from openhands.events.action.action import Action, ActionSecurityRisk
from openhands.events.event import Event
from openhands.events.stream import EventStream
from openhands.security.analyzer import SecurityAnalyzer


class LLMRiskAnalyzer(SecurityAnalyzer):
    """Security analyzer that respects LLM-provided risk assessments."""

    def __init__(
        self, event_stream: EventStream, settings: dict[str, Any] | None = None
    ) -> None:
        """Initializes a new instance of the LLMRiskAnalyzer class.

        Args:
            event_stream: The event stream to listen for events.
            settings: Optional settings for the analyzer.
        """
        super().__init__(event_stream)
        self.settings = settings or {}

    async def handle_api_request(self, request: Request) -> Any:
        """Handles the incoming API request."""
        return {'status': 'ok'}

    def _get_risk_level_mapping(self) -> dict[str, ActionSecurityRisk]:
        """Returns the mapping from string risk levels to ActionSecurityRisk enum values."""
        return {
            'LOW': ActionSecurityRisk.LOW,
            'MEDIUM': ActionSecurityRisk.MEDIUM,
            'HIGH': ActionSecurityRisk.HIGH,
        }

    async def security_risk(self, event: Action) -> ActionSecurityRisk:
        """Evaluates the Action for security risks and returns the risk level.

        This analyzer checks if the action has a 'security_risk' attribute set by the LLM.
        If it does, it uses that value. Otherwise, it returns UNKNOWN.
        """
        # Check if the action has a security_risk attribute set by the LLM
        if not hasattr(event, 'security_risk'):
            return ActionSecurityRisk.UNKNOWN

        security_risk = getattr(event, 'security_risk')
        risk_mapping = self._get_risk_level_mapping()

        if security_risk in risk_mapping:
            logger.info(f'Using LLM-provided risk assessment: {security_risk}')
            return risk_mapping[security_risk]

        # Default to UNKNOWN if security_risk value is not recognized
        logger.warning(f'Unrecognized security_risk value: {security_risk}')
        return ActionSecurityRisk.UNKNOWN

    async def act(self, event: Event) -> None:
        """Performs an action based on the analyzed event.

        For now, this just logs the risk level.
        """
        if isinstance(event, Action) and hasattr(event, 'security_risk'):
            logger.info(
                f'Action {event.__class__.__name__} has LLM-provided risk: {event.security_risk}'
            )
