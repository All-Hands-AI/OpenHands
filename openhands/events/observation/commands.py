import json
import re
from dataclasses import dataclass, field
from typing import Self

from pydantic import BaseModel

from openhands.core.logger import openhands_logger as logger
from openhands.core.schema import ObservationType
from openhands.events.observation.observation import Observation

CMD_OUTPUT_METADATA_PS1_REGEX = re.compile(
    r'###PS1JSON###\n(.*?)###PS1END###\n', re.DOTALL
)


class CmdOutputMetadata(BaseModel):
    """Additional metadata captured from PS1"""

    exit_code: int = -1
    username: str | None = None
    hostname: str | None = None
    working_dir: str | None = None
    py_interpreter_path: str | None = None

    @classmethod
    def to_ps1_prompt(cls) -> str:
        """Convert the required metadata into a PS1 prompt."""
        prompt = '###PS1JSON###\n'
        prompt += json.dumps(
            {
                'exit_code': '$?',
                'username': r'\u',
                'hostname': r'\h',
                'working_dir': r'\w',
                'py_interpreter_path': '$(which python 2>/dev/null || echo "")',
            },
            indent=2,
        )
        prompt += '\n###PS1END###\n'
        return prompt

    @classmethod
    def contains_ps1_metadata(cls, actual_ps1: str) -> bool:
        return CMD_OUTPUT_METADATA_PS1_REGEX.search(actual_ps1) is not None

    @classmethod
    def from_ps1(cls, actual_ps1: str) -> Self:
        """Extract the required metadata from a PS1 prompt."""
        matches = list(CMD_OUTPUT_METADATA_PS1_REGEX.finditer(actual_ps1))
        if len(matches) > 1:
            raise ValueError("Multiple PS1 metadata blocks detected. Expected only one.")
        if not matches:
            return cls()
        try:
            metadata = json.loads(matches[0].group(1))
            return cls(**metadata)
        except json.JSONDecodeError:
            logger.warning(f'Failed to parse PS1 metadata: {matches[0].group(1)}')
            return cls()


@dataclass
class CmdOutputObservation(Observation):
    """This data class represents the output of a command."""

    command_id: int
    command: str
    observation: str = ObservationType.RUN
    # Additional metadata captured from PS1
    metadata: CmdOutputMetadata = field(default_factory=CmdOutputMetadata)
    # Whether the command output should be hidden from the user
    hidden: bool = False

    @property
    def exit_code(self) -> int:
        return self.metadata.exit_code

    @property
    def error(self) -> bool:
        return self.exit_code != 0

    @property
    def message(self) -> str:
        return f'Command `{self.command}` executed with exit code {self.exit_code}.'

    def __str__(self) -> str:
        return f'**CmdOutputObservation (source={self.source}, exit code={self.exit_code}, metadata={json.dumps(self.metadata.model_dump(), indent=2)})**\n{self.content}'


@dataclass
class IPythonRunCellObservation(Observation):
    """This data class represents the output of a IPythonRunCellAction."""

    code: str
    observation: str = ObservationType.RUN_IPYTHON

    @property
    def error(self) -> bool:
        return False  # IPython cells do not return exit codes

    @property
    def message(self) -> str:
        return 'Code executed in IPython cell.'

    def __str__(self) -> str:
        return f'**IPythonRunCellObservation**\n{self.content}'
