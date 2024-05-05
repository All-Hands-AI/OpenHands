from dataclasses import dataclass

from opendevin.core.schema import ActionType

from .action import Action


@dataclass
class UserMessageAction(Action):
    action: str = ActionType.USER_MESSAGE
