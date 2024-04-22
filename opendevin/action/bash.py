import os
import pathlib
from dataclasses import dataclass
from typing import TYPE_CHECKING

from .base import ExecutableAction
from opendevin import config
from opendevin.schema import ActionType, ConfigType

if TYPE_CHECKING:
    from opendevin.controller import AgentController
    from opendevin.observation import CmdOutputObservation


@dataclass
class CmdRunAction(ExecutableAction):
    command: str
    thought: str = ''
    background: bool = False
    action: str = ActionType.RUN

    async def run(self, controller: 'AgentController') -> 'CmdOutputObservation':
        return controller.action_manager.run_command(self.command, self.background)

    @property
    def message(self) -> str:
        return f'Running command: {self.command}'

    def __str__(self) -> str:
        ret = '**CmdRunAction**\n'
        if self.thought:
            ret += f'THOUGHT:{self.thought}\n'
        ret += f'COMMAND:\n{self.command}'
        return ret


@dataclass
class CmdKillAction(ExecutableAction):
    id: int
    action: str = ActionType.KILL

    async def run(self, controller: 'AgentController') -> 'CmdOutputObservation':
        return controller.action_manager.kill_command(self.id)

    @property
    def message(self) -> str:
        return f'Killing command: {self.id}'

    def __str__(self) -> str:
        return f'**CmdKillAction**\n{self.id}'


@dataclass
class IPythonRunCellAction(ExecutableAction):
    code: str
    thought: str = ''
    action: str = ActionType.RUN

    async def run(self, controller: 'AgentController') -> 'CmdOutputObservation':
        # echo "import math" | execute_cli
        # write code to a temporary file and pass it to `execute_cli` via stdin
        tmp_filepath = os.path.join(
            config.get(ConfigType.WORKSPACE_BASE),
            '.tmp', '.execution_tmp.py'
        )
        pathlib.Path(os.path.dirname(tmp_filepath)).mkdir(parents=True, exist_ok=True)
        with open(tmp_filepath, 'w') as tmp_file:
            tmp_file.write(self.code)

        tmp_filepath_inside_sandbox = os.path.join(
            config.get(ConfigType.WORKSPACE_MOUNT_PATH_IN_SANDBOX),
            '.tmp', '.execution_tmp.py'
        )
        return controller.action_manager.run_command(
            f'execute_cli < {tmp_filepath_inside_sandbox}',
            background=False
        )

    def __str__(self) -> str:
        ret = '**IPythonRunCellAction**\n'
        if self.thought:
            ret += f'THOUGHT:{self.thought}\n'
        ret += f'CODE:\n{self.code}'
        return ret

    @property
    def message(self) -> str:
        return f'Running Python code interactively: {self.code}'
