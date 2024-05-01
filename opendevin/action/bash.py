from dataclasses import dataclass
from typing import TYPE_CHECKING

from opendevin.schema import ActionType

from .base import ExecutableAction

if TYPE_CHECKING:
    from opendevin.controller import AgentController
    from opendevin.observation import CmdOutputObservation, Observation


@dataclass
class CmdRunAction(ExecutableAction):
    command: str
    background: bool = False
    action: str = ActionType.RUN

    async def run(self, controller: 'AgentController') -> 'Observation':
        return controller.action_manager.run_command(self.command, self.background)

    @property
    def message(self) -> str:
        return f'Running command: {self.command}'


@dataclass
class CmdKillAction(ExecutableAction):
    id: int
    action: str = ActionType.KILL

    async def run(self, controller: 'AgentController') -> 'CmdOutputObservation':
        return controller.action_manager.kill_command(self.id)

    @property
    def message(self) -> str:
        return f'Killing command: {self.id}'
