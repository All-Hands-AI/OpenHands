"""Tool use action for OpenHands."""

from dataclasses import dataclass
from typing import Any

from openhands.core.schema.action import ActionType
from openhands.events.action.action import Action


@dataclass
class ToolUseAction(Action):
    """Action for using a tool."""

    tool_name: str
    tool_input: dict[str, Any]
    thought: str = ''
    action: str = ActionType.TOOL_USE

    @property
    def message(self) -> str:
        """Get the message for this action.

        Returns:
            A string message describing the tool use
        """
        return f'Using tool: {self.tool_name}'
