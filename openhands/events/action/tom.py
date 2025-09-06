"""Tom-related action types for OpenHands."""

from dataclasses import dataclass
from typing import Optional

from openhands.core.schema import ActionType
from openhands.events.action.action import Action


@dataclass
class ConsultTomAgentAction(Action):
    """Action to consult Tom agent for guidance."""

    content: str
    use_user_message: bool = True
    custom_query: Optional[str] = None
    action: str = ActionType.CONSULT_TOM_AGENT
