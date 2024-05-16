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


@dataclass
class BrowseInteractiveAction(Action):
    browser_actions: str
    thought: str = ''
    action: str = ActionType.BROWSE_INTERACTIVE
    runnable: ClassVar[bool] = True

    @property
    def message(self) -> str:
        return f'Executing browser actions: {self.browser_actions}'
