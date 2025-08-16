from typing import Any

from fastapi import Request

from openhands.events.action.action import Action, ActionSafetyRisk
from openhands.security.analyzer import SecurityAnalyzer


class NoneAnalyzer(SecurityAnalyzer):
    """Security analyzer that treats every action as high risk, requiring confirmation for all commands."""

    async def safety_risk(self, event: Action) -> ActionSafetyRisk:
        """Always returns HIGH risk to require confirmation for every action."""
        return ActionSafetyRisk.HIGH

    async def handle_api_request(self, request: Request) -> Any:
        """Handle API requests (not used for none analyzer)."""
        return {'status': 'none_analyzer'}
