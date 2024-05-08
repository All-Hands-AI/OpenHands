from typing import ClassVar

from opendevin.core.schema import ActionType

from .action import Action


class MessageAction(Action):
    content: str
    wait_for_response: bool = False
    action: ClassVar[str] = ActionType.MESSAGE

    @property
    def message(self) -> str:
        return self.content
