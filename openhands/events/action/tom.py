"""Tom-related action types for OpenHands."""

from dataclasses import dataclass

from openhands.core.schema import ActionType
from openhands.events.action.action import Action


@dataclass
class ImproveInstructionAction(Action):
    """Action to improve user instructions using Tom agent."""

    content: str
    action: str = ActionType.IMPROVE_INSTRUCTION
