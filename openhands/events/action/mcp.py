from dataclasses import dataclass
from typing import ClassVar

from openhands.core.schema import ActionType
from openhands.events.action.action import Action, ActionSecurityRisk


@dataclass
class McpAction(Action):
    name: str
    arguments: str | None = None
    thought: str = ''
    sid: str | None = None
    action: str = ActionType.MCP
    runnable: ClassVar[bool] = True
    security_risk: ActionSecurityRisk | None = None

    def __init__(
        self,
        name: str,
        arguments: str,
        sid: str | None = None,
        thought: str = '',
        **kwargs,
    ):
        # Initialize first as Action with no args
        super().__init__()
        # Then assign our specific fields
        self.name = name
        self.arguments = arguments
        self.sid = sid
        self.thought = thought

    @property
    def message(self) -> str:
        return (
            f'I am interacting with the MCP server with name: {self.name}\n'
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
