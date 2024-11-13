from dataclasses import dataclass
from typing import ClassVar

from openhands.core.schema import ActionType
from openhands.events.action.action import (
    Action,
    ActionConfirmationStatus,
    ActionSecurityRisk,
)


@dataclass
class ReplayCmdRunAction(Action):
    command: str
    thought: str = ''
    blocking: bool = True
    keep_prompt: bool = False
    hidden: bool = False
    action: str = ActionType.RUN_REPLAY
    runnable: ClassVar[bool] = True
    confirmation_state: ActionConfirmationStatus = ActionConfirmationStatus.CONFIRMED
    security_risk: ActionSecurityRisk | None = None
    recording_id: str = ''
    session_id: str = ''

    @property
    def message(self) -> str:
        return f'Running replay command: {self.command}'

    def __str__(self) -> str:
        ret = f'**ReplayCmdRunAction (source={self.source})**\n'
        if self.thought:
            ret += f'THOUGHT: {self.thought}\n'
        ret += f'COMMAND:\n{self.command}'
        return ret
