from typing import Any

from fastapi import Request

from openhands.events.action.action import Action, ActionSecurityRisk


class SecurityAnalyzer:
    """Security analyzer that analyzes agent actions for security risks."""

    def __init__(self) -> None:
        """Initializes a new instance of the SecurityAnalyzer class."""
        pass

    async def handle_api_request(self, request: Request) -> Any:
        """Handles the incoming API request."""
        raise NotImplementedError(
            'Need to implement handle_api_request method in SecurityAnalyzer subclass'
        )

    async def security_risk(self, action: Action) -> ActionSecurityRisk:
        """Evaluates the Action for security risks and returns the risk level."""
        raise NotImplementedError(
            'Need to implement security_risk method in SecurityAnalyzer subclass'
        )

    async def close(self) -> None:
        """Cleanup resources allocated by the SecurityAnalyzer."""
        pass
