from dataclasses import dataclass

from openhands.core.schema import ObservationType
from openhands.events.observation.observation import Observation


@dataclass
class ReplayCmdOutputObservation(Observation):
    """This data class represents the output of a replay command."""

    command_id: int
    command: str
    exit_code: int = 0
    hidden: bool = False
    observation: str = ObservationType.RUN_REPLAY
    interpreter_details: str = ''

    @property
    def error(self) -> bool:
        return self.exit_code != 0

    @property
    def message(self) -> str:
        return f'Command `{self.command}` executed with exit code {self.exit_code}.'

    def __str__(self) -> str:
        return f'**ReplayCmdOutputObservation (source={self.source}, exit code={self.exit_code})**\n{self.content}'
