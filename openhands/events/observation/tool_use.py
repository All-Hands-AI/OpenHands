from dataclasses import dataclass
from typing import ClassVar

from openhands.core.schema import ObservationType
from openhands.events.observation.observation import Observation


@dataclass
class ToolUseObservation(Observation):
    """
    This data class represents the result of a tool use action.
    """

    observation: str = ObservationType.TOOL_USE
    runnable: ClassVar[bool] = False
    content: str = ''
    tool_call_id: str = ''

    @property
    def message(self) -> str:
        return f'Tool use result:\n{self.content}'

    def __str__(self) -> str:
        ret = '**ToolUseObservation**\n'
        ret += f'CONTENT: {self.content}'
        return ret
