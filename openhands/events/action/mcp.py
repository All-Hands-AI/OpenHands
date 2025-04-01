from dataclasses import dataclass
from typing import Any, ClassVar

from openhands.core.schema import ActionType
from openhands.events.action.action import Action


@dataclass
class MCPCallToolAction(Action):
    runnable: ClassVar[bool] = True
    thought: str = ''
    tool_name: str = ''
    kwargs: dict[str, Any] | None = None
    action: str = ActionType.MCP_CALL_TOOL

    @property
    def message(self) -> str:
        msg: str = f'Calling MCP tool `{self.tool_name}` with arguments: {self.kwargs}'
        return msg
