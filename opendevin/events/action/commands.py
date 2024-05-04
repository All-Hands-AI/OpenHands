from dataclasses import dataclass
from typing import TYPE_CHECKING

from opendevin.core.schema import ActionType

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
        obs = controller.action_manager.run_command(
            ('cat > /tmp/opendevin_jupyter_temp.py <<EOL\n' f'{self.code}\n' 'EOL'),
            background=False,
        )

        # run the code
        obs = controller.action_manager.run_command(
            ('cat /tmp/opendevin_jupyter_temp.py | execute_cli'), background=False
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
