from typing import Any

from fastapi import Request

from openhands.events.action.action import Action, ActionSecurityRisk
from openhands.security.analyzer import SecurityAnalyzer


class NoneAnalyzer(SecurityAnalyzer):
    """Security analyzer that treats every action as high risk, requiring confirmation for all commands."""

    async def security_risk(self, event: Action) -> ActionSecurityRisk:
        """Always returns HIGH risk to require confirmation for every action."""
        return ActionSecurityRisk.HIGH

    async def handle_api_request(self, request: Request) -> Any:
        """Handle API requests (not used for none analyzer)."""
        return {"status": "none_analyzer"}