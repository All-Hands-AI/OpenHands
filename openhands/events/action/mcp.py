from dataclasses import dataclass, field
from typing import ClassVar

from openhands.core.schema import ActionType
from openhands.events.action.action import Action


@dataclass
class MCPCallToolAction(Action):
    kwargs: dict = field(default_factory=dict)
    tool_name: str = ''
    action: str = ActionType.MCP_CALL_TOOL
    runnable: ClassVar[bool] = True

    @property
    def message(self) -> str:
        msg: str = f'Calling MCP tool `{self.tool_name}` with arguments: {self.kwargs}'
        return msg
