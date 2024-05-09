from dataclasses import dataclass

from opendevin.core.schema import ActionType

from .action import Action


@dataclass
class CmdRunAction(Action):
    command: str
    background: bool = False
    thought: str = ''
    action: str = ActionType.RUN

    def runnable(self) -> bool:
        return True

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

    def runnable(self) -> bool:
        return True

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

    def runnable(self) -> bool:
        return True

    def __str__(self) -> str:
        ret = '**IPythonRunCellAction**\n'
        if self.thought:
            ret += f'THOUGHT:{self.thought}\n'
        ret += f'CODE:\n{self.code}'
        return ret

    @property
    def message(self) -> str:
        return f'Running Python code interactively: {self.code}'
