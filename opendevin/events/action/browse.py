from typing import ClassVar

from pydantic.dataclasses import dataclass

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
