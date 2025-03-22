from dataclasses import dataclass
from typing import ClassVar

from openhands.core.schema import ActionType
from openhands.events.action.action import Action


@dataclass
class SearchAction(Action):
    query: str
    thought: str = ''
    action: str = ActionType.SEARCH
    runnable: ClassVar[bool] = True

    @property
    def message(self) -> str:
        return f'I am querying the search engine to search for {self.query}'

    def __str__(self) -> str:
        ret = '**SearchAction**\n'
        if self.thought:
            ret += f'THOUGHT: {self.thought}\n'
        ret += f'QUERY: {self.query}'
        return ret
