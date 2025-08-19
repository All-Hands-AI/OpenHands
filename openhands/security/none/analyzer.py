"""Security analyzer that always returns HIGH risk for all actions (always confirm)."""

from typing import Any

from fastapi import Request

from openhands.events.action.action import Action, ActionSecurityRisk
from openhands.security.analyzer import SecurityAnalyzer


class NoneSecurityAnalyzer(SecurityAnalyzer):
    """Security analyzer that always returns HIGH risk, ensuring all actions require confirmation."""

    async def handle_api_request(self, request: Request) -> Any:
        """Handles the incoming API request."""
        return {'status': 'ok'}

    async def security_risk(self, event: Action) -> ActionSecurityRisk:
        """Always returns HIGH risk to ensure all actions require confirmation.
        
        This analyzer implements the "None (always confirm)" behavior by treating
        all actions as high risk, which triggers the confirmation dialog.
        """
        return ActionSecurityRisk.HIGH