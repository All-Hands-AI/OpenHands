from dataclasses import dataclass
from typing import ClassVar

from openhands.core.logger import openhands_logger as logger
from openhands.core.schema import ActionType
from openhands.events.action.action import (
    Action,
    ActionConfirmationStatus,
    ActionSecurityRisk,
)


@dataclass
class CmdRunAction(Action):
    command: str
    # When `command` is empty, it will be used to print the current tmux window
    thought: str = ''
    blocking: bool = False
    # If blocking is True, the command will be run in a blocking manner.
    # e.g., it will NOT return early due to soft timeout.
    hidden: bool = False
    action: str = ActionType.RUN
    runnable: ClassVar[bool] = True
    confirmation_state: ActionConfirmationStatus = ActionConfirmationStatus.CONFIRMED
    security_risk: ActionSecurityRisk | None = None

    def __init__(
        self,
        command: str,
        thought: str = '',
        blocking: bool = False,
        hidden: bool = False,
        action: str = ActionType.RUN,
        confirmation_state: ActionConfirmationStatus = ActionConfirmationStatus.CONFIRMED,
        security_risk: ActionSecurityRisk | None = None,
        **kwargs,
    ):
        self.command = command
        self.thought = thought
        self.blocking = blocking
        self.hidden = hidden
        self.action = action
        self.confirmation_state = confirmation_state
        self.security_risk = security_risk
        logger.debug(
            f'CmdRunAction ignored kwargs (likely due to legacy serialization): {kwargs}'
        )

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
    include_extra: bool = (
        True  # whether to include CWD & Python interpreter in the output
    )
    action: str = ActionType.RUN_IPYTHON
    runnable: ClassVar[bool] = True
    confirmation_state: ActionConfirmationStatus = ActionConfirmationStatus.CONFIRMED
    security_risk: ActionSecurityRisk | None = None
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
