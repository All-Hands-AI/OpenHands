from dataclasses import dataclass

from opendevin.core.schema import ActionType

from .action import Action


@dataclass
class MessageAction(Action):
    content: str
    action: str = ActionType.MESSAGE

    @property
    def message(self) -> str:
        return self.content
