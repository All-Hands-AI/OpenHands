import os
import pathlib
from dataclasses import dataclass
from typing import TYPE_CHECKING

from opendevin.core import config
from opendevin.core.schema import ActionType, ConfigType

from .action import Action

if TYPE_CHECKING:
    from opendevin.controller import AgentController
    from opendevin.events.observation import CmdOutputObservation, Observation

from opendevin.events.observation import IPythonRunCellObservation


@dataclass
class CmdRunAction(Action):
    command: str
    background: bool = False
    thought: str = ''
    action: str = ActionType.RUN

    async def run(self, controller: 'AgentController') -> 'Observation':
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
class CmdKillAction(Action):
    id: int
    thought: str = ''
    action: str = ActionType.KILL

    async def run(self, controller: 'AgentController') -> 'CmdOutputObservation':
        return controller.action_manager.kill_command(self.id)

    @property
    def message(self) -> str:
        return f'Killing command: {self.id}'

    def __str__(self) -> str:
        return f'**CmdKillAction**\n{self.id}'


@dataclass
class IPythonRunCellAction(Action):
    code: str
    thought: str = ''
    action: str = ActionType.RUN_IPYTHON

    async def run(self, controller: 'AgentController') -> 'IPythonRunCellObservation':
        # echo "import math" | execute_cli
        # write code to a temporary file and pass it to `execute_cli` via stdin
        tmp_filepath = os.path.join(
            config.get(ConfigType.WORKSPACE_BASE), '.tmp', '.ipython_execution_tmp.py'
        )
        pathlib.Path(os.path.dirname(tmp_filepath)).mkdir(parents=True, exist_ok=True)
        with open(tmp_filepath, 'w') as tmp_file:
            tmp_file.write(self.code)

        tmp_filepath_inside_sandbox = os.path.join(
            config.get(ConfigType.WORKSPACE_MOUNT_PATH_IN_SANDBOX),
            '.tmp',
            '.ipython_execution_tmp.py',
        )
        obs = controller.action_manager.run_command(
            f'execute_cli < {tmp_filepath_inside_sandbox}', background=False
        )
        return IPythonRunCellObservation(content=obs.content, code=self.code)

    def __str__(self) -> str:
        ret = '**IPythonRunCellAction**\n'
        if self.thought:
            ret += f'THOUGHT:{self.thought}\n'
        ret += f'CODE:\n{self.code}'
        return ret

    @property
    def message(self) -> str:
        return f'Running Python code interactively: {self.code}'
