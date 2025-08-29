from dataclasses import dataclass

from openhands.core.schema import ActionType
from openhands.events.action.action import Action


@dataclass
class InitPyodideAction(Action):
    content: str
    wait_for_response: bool = False
    action: str = ActionType.INIT_PYODIDE

    @property
    def message(self) -> str:
        return self.content

    def __str__(self) -> str:
        ret = '**InitPyodideAction**'
        ret += f'CONTENT: {self.content}'
        return ret
