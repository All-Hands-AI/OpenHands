from dataclasses import dataclass, field
from typing import Optional

from opendevin.core.schema import ActionType
from opendevin.events.action.action import ActionSecurityRisk

from .action import Action


@dataclass
class MessageAction(Action):
    content: str
    wait_for_response: bool = False
    action: str = ActionType.MESSAGE

    @property
    def message(self) -> str:
        return self.content

    def __str__(self) -> str:
        ret = f'**MessageAction** (source={self.source})\n'
        ret += f'CONTENT: {self.content}'
        return ret
