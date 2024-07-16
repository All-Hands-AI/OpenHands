from dataclasses import dataclass
from typing import ClassVar

from opendevin.core.schema import ActionType

from .action import Action, ActionConfirmationStatus


@dataclass
class CmdRunAction(Action):
    command: str
    thought: str = ''
    action: str = ActionType.RUN
    runnable: ClassVar[bool] = True
    is_confirmed: ActionConfirmationStatus = ActionConfirmationStatus.CONFIRMED

    @property
    def message(self) -> str:
        return f'Running command: {self.command}'

    def __str__(self) -> str:
        ret = f'**CmdRunAction (source={self.source})**\n'
        if self.thought:
            ret += f'THOUGHT: {self.thought}\n'
        ret += f'COMMAND:\n{self.command}'
        return ret


@dataclass
class IPythonRunCellAction(Action):
    code: str
    thought: str = ''
    action: str = ActionType.RUN_IPYTHON
    runnable: ClassVar[bool] = True
    is_confirmed: ActionConfirmationStatus = ActionConfirmationStatus.CONFIRMED
    kernel_init_code: str = ''  # code to run in the kernel (if the kernel is restarted)

    def __str__(self) -> str:
        ret = '**IPythonRunCellAction**\n'
        if self.thought:
            ret += f'THOUGHT: {self.thought}\n'
        ret += f'CODE:\n{self.code}'
        return ret

    @property
    def message(self) -> str:
        return f'Running Python code interactively: {self.code}'
