from dataclasses import dataclass, field
from typing import Any, ClassVar

from openhands.core.schema import ActionType
from openhands.events.action import Action, ActionSecurityRisk, Thought


@dataclass
class MCPAction(Action):
    name: str
    arguments: dict[str, Any] = field(default_factory=dict)
    thought: Thought = field(default_factory=Thought)
    action: str = ActionType.MCP
    runnable: ClassVar[bool] = True
    security_risk: ActionSecurityRisk = ActionSecurityRisk.UNKNOWN

    @property
    def message(self) -> str:
        return (
            f'I am interacting with the MCP server with name:\n'
            f'```\n{self.name}\n```\n'
            f'and arguments:\n'
            f'```\n{self.arguments}\n```'
        )

    def __str__(self) -> str:
        ret = '**MCPAction**\n'
        if self.thought:
            ret += f'THOUGHT: {self.thought}\n'
        ret += f'NAME: {self.name}\n'
        ret += f'ARGUMENTS: {self.arguments}'
        return ret
