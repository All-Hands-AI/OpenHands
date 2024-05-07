from dataclasses import dataclass
from typing import TYPE_CHECKING

from opendevin.core.schema import ActionType

from .action import Action

if TYPE_CHECKING:
    pass


@dataclass
class BrowseURLAction(Action):
    url: str
    thought: str = ''
    action: str = ActionType.BROWSE

    @property
    def runnable(self) -> bool:
        return True

    @property
    def message(self) -> str:
        return f'Browsing URL: {self.url}'
