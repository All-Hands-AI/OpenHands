from typing import ClassVar

from opendevin.core.schema import ObservationType

from .observation import Observation


class CmdOutputObservation(Observation):
    """
    This data class represents the output of a command.
    """

    command_id: int
    command: str
    exit_code: int = 0
    observation: ClassVar[str] = ObservationType.RUN

    @property
    def error(self) -> bool:
        return self.exit_code != 0

    @property
    def message(self) -> str:
        return f'Command `{self.command}` executed with exit code {self.exit_code}.'


class IPythonRunCellObservation(Observation):
    """
    This data class represents the output of a IPythonRunCellAction.
    """

    code: str
    observation: ClassVar[str] = ObservationType.RUN_IPYTHON

    @property
    def error(self) -> bool:
        return False  # IPython cells do not return exit codes

    @property
    def message(self) -> str:
        return 'Coded executed in IPython cell.'
