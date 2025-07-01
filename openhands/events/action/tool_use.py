from dataclasses import dataclass, field
from typing import Any, ClassVar

from openhands.core.schema import ActionType
from openhands.events.action.action import Action, ActionSecurityRisk


@dataclass
class ToolUseAction(Action):
    name: str
    arguments: dict[str, Any] = field(default_factory=dict)
    thought: str = ''
    action: str = ActionType.TOOL_USE
    runnable: ClassVar[bool] = True
    security_risk: ActionSecurityRisk | None = None
    tool_call_id: str = ''

    @property
    def message(self) -> str:
        return (
            f'I am using the tool:\n'
            f'```\n{self.name}\n```\n'
            f'with arguments:\n'
            f'```\n{self.arguments}\n```'
        )

    def __str__(self) -> str:
        ret = '**ToolUseAction**\n'
        if self.thought:
            ret += f'THOUGHT: {self.thought}\n'
        ret += f'NAME: {self.name}\n'
        ret += f'ARGUMENTS: {self.arguments}'
        return ret
