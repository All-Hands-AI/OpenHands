from dataclasses import dataclass
from typing import ClassVar

from opendevin.core.schema import ActionType

from .action import Action


@dataclass
class BrowseURLAction(Action):
    url: str
    thought: str = ''
    action: str = ActionType.BROWSE
    runnable: ClassVar[bool] = True

    @property
    def message(self) -> str:
        return f'Browsing URL: {self.url}'
