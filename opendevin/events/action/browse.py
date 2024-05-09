from dataclasses import dataclass

from opendevin.core.schema import ActionType

from .action import Action


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
