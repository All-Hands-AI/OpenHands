from typing import Any

from fastapi import Request

from openhands.core.logger import openhands_logger as logger
from openhands.events.action.action import (
    Action,
    ActionConfirmationStatus,
    ActionSecurityRisk,
)
from openhands.events.action.commands import CmdRunAction, IPythonRunCellAction
from openhands.events.event import Event
from openhands.events.stream import EventStream
from openhands.security.analyzer import SecurityAnalyzer


class CommandApprovalAnalyzer(SecurityAnalyzer):
    """Security analyzer that automatically approves commands based on patterns and previously approved commands."""

    def __init__(
        self,
        event_stream: EventStream,
        policy: str | None = None,
        sid: str | None = None,
    ) -> None:
        """Initializes a new instance of the CommandApprovalAnalyzer class."""
        super().__init__(event_stream)

    async def handle_api_request(self, request: Request) -> Any:
        """Handles the incoming API request."""
        # This analyzer doesn't need to handle API requests
        return {'message': "Command approval analyzer doesn't support API requests"}

    async def security_risk(self, event: Action) -> ActionSecurityRisk:
        """Evaluates the Action for security risks and returns the risk level.

        For command approval analyzer, we always return LOW risk level,
        but we set the confirmation_state based on whether the command is approved.
        """
        # Get the security config from the global config
        from openhands.core.config import get_config

        config = get_config()

        # Only process CmdRunAction and IPythonRunCellAction
        if isinstance(event, CmdRunAction) and hasattr(
            config.security, 'is_command_approved'
        ):
            command = event.command
            if config.security.is_command_approved(command):
                event.confirmation_state = ActionConfirmationStatus.CONFIRMED
                logger.info(f'Command automatically approved: {command}')

        elif isinstance(event, IPythonRunCellAction) and hasattr(
            config.security, 'is_command_approved'
        ):
            code = event.code
            if config.security.is_command_approved(code):
                event.confirmation_state = ActionConfirmationStatus.CONFIRMED
                logger.info(f'Python code automatically approved: {code}')

        # Always return LOW risk level - we're not evaluating risk, just auto-approving
        return ActionSecurityRisk.LOW

    async def act(self, event: Event) -> None:
        """Performs an action based on the analyzed event.

        This analyzer doesn't need to perform any actions since command approval
        is handled directly in the CLI interface.
        """
        pass
