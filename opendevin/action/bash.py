from dataclasses import dataclass
from typing import TYPE_CHECKING

from .base import ExecutableAction
from opendevin.schema import ActionType

if TYPE_CHECKING:
    from opendevin.controller import AgentController
    from opendevin.observation import CmdOutputObservation


@dataclass
class CmdRunAction(ExecutableAction):
    command: str
    background: bool = False
    action: str = ActionType.RUN

    def run(self, controller: "AgentController") -> "CmdOutputObservation":
        return controller.command_manager.run_command(self.command, self.background)

    @property
    def message(self) -> str:
        return f"Running command: {self.command}"


@dataclass
class CmdKillAction(ExecutableAction):
    id: int
    action: str = ActionType.KILL

    def run(self, controller: "AgentController") -> "CmdOutputObservation":
        return controller.command_manager.kill_command(self.id)

    @property
    def message(self) -> str:
        return f"Killing command: {self.id}"
