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
    # Command args to be passed to @replay/cli.
    command: str

    # The thought/prompt message that triggered this action.
    thought: str = ''

    blocking: bool = True
    keep_prompt: bool = False
    hidden: bool = False
    action: str = ActionType.RUN_REPLAY
    runnable: ClassVar[bool] = True
    confirmation_state: ActionConfirmationStatus = ActionConfirmationStatus.CONFIRMED
    security_risk: ActionSecurityRisk | None = None

    # Whether to execute the command from the workspace directory, independent of CWD.
    in_workspace_dir: bool = True

    # List of strings that need to be written to text files, and then provided as argument to command.
    # NOTE: Sometimes this is necessary to avoid bash encoding pitfalls.
    file_arguments: list[str] | None = None

    # Other Replay fields.
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
