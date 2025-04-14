from dataclasses import dataclass
from typing import ClassVar

from openhands.core.schema import ActionType
from openhands.events.action.action import Action, ActionSecurityRisk


@dataclass
class McpAction(Action):
    name: str
    arguments: str | None = None
    thought: str = ''
    action: str = ActionType.MCP
    runnable: ClassVar[bool] = True
    security_risk: ActionSecurityRisk | None = None

    @property
    def message(self) -> str:
        return (
            f'I am interacting with the MCP server with name:\n'
            f'```\n{self.name}\n```\n'
            f'and arguments:\n'
            f'```\n{self.arguments}\n```'
        )

    def __str__(self) -> str:
        ret = '**McpAction**\n'
        if self.thought:
            ret += f'THOUGHT: {self.thought}\n'
        ret += f'NAME: {self.name}\n'
        ret += f'ARGUMENTS: {self.arguments}'
        return ret
