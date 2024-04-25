import os
import tempfile
from dataclasses import dataclass
from typing import TYPE_CHECKING

from .base import ExecutableAction
from opendevin.schema import ActionType
from opendevin.logger import opendevin_logger as logger

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
        # create a temporary file
        tmp_file = tempfile.NamedTemporaryFile(mode='w', delete=False)
        tmp_filepath = tmp_file.name
        tmp_file.write(self.code)
        tmp_file.close()

        # move the file to the sandbox
        controller.action_manager.sandbox.copy_to(
            tmp_filepath,
            '/tmp/.execution_tmp.py'
        )
        ret = controller.action_manager.run_command(
            'execute_cli < /tmp/.execution_tmp.py',
            background=False
        )
        _delete_res = controller.action_manager.run_command(
            'rm /tmp/.execution_tmp.py',
            background=False
        )
        if _delete_res.exit_code != 0:
            logger.warning(f'Failed to delete temporary file for Jupyter: {_delete_res.content}')
        # remove the temporary file on the host
        os.remove(tmp_filepath)
        return ret

    def __str__(self) -> str:
        ret = '**IPythonRunCellAction**\n'
        if self.thought:
            ret += f'THOUGHT:{self.thought}\n'
        ret += f'CODE:\n{self.code}'
        return ret

    @property
    def message(self) -> str:
        return f'Running Python code interactively: {self.code}'
