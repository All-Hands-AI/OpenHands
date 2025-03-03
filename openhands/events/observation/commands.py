import json
import re
import traceback
from dataclasses import dataclass, field
from typing import Self

from pydantic import BaseModel

from openhands.core.logger import openhands_logger as logger
from openhands.core.schema import ObservationType
from openhands.events.observation.observation import Observation

CMD_OUTPUT_PS1_BEGIN = '\n###PS1BEGIN###\n'
CMD_OUTPUT_PS1_END = '\n###PS1END###'
CMD_OUTPUT_METADATA_PS1_REGEX = re.compile(
    r'###PS1BEGIN###\s*\n'
    r'PID=([^\n]*)\s*\n'
    r'EXIT_CODE=([^\n]*)\s*\n'
    r'USERNAME=([^\n]*)\s*\n'
    r'HOSTNAME=([^\n]*)\s*\n'
    r'WORKING_DIR=([^\n]*)\s*\n'
    r'PY_INTERPRETER_PATH=([^\n]*)\s*\n'
    r'###PS1END###',
    re.MULTILINE | re.DOTALL,
)


class CmdOutputMetadata(BaseModel):
    """Additional metadata captured from PS1"""

    exit_code: int = -1
    pid: int = -1
    username: str | None = None
    hostname: str | None = None
    working_dir: str | None = None
    py_interpreter_path: str | None = None
    prefix: str = ''  # Prefix to add to command output
    suffix: str = ''  # Suffix to add to command output

    @classmethod
    def to_ps1_prompt(cls) -> str:
        """Convert the required metadata into a PS1 prompt."""
        return (
            CMD_OUTPUT_PS1_BEGIN +
            'PID=$!\n' +
            'EXIT_CODE=$?\n' +
            r'USERNAME=\u\n' +
            r'HOSTNAME=\h\n' +
            r'WORKING_DIR=$(pwd)\n' +
            r'PY_INTERPRETER_PATH=$(which python 2>/dev/null || echo "")\n' +
            CMD_OUTPUT_PS1_END + '\n'  # Ensure there's a newline at the end
        )

    @classmethod
    def matches_ps1_metadata(cls, string: str) -> list[re.Match[str]]:
        return list(CMD_OUTPUT_METADATA_PS1_REGEX.finditer(string))

    @classmethod
    def from_ps1_match(cls, match: re.Match[str]) -> Self:
        """Extract the required metadata from a PS1 prompt."""
        pid = match.group(1)
        exit_code = match.group(2)
        username = match.group(3)
        hostname = match.group(4)
        working_dir = match.group(5)
        py_interpreter_path = match.group(6)

        try:
            pid = int(float(str(pid)))
        except (ValueError, TypeError):
            pid = -1

        try:
            exit_code = int(float(str(exit_code)))
        except (ValueError, TypeError):
            logger.warning(f'Failed to parse exit code: {exit_code}. Setting to -1.')
            exit_code = -1

        return cls(
            pid=pid,
            exit_code=exit_code,
            username=username,
            hostname=hostname,
            working_dir=working_dir,
            py_interpreter_path=py_interpreter_path,
        )


@dataclass
class CmdOutputObservation(Observation):
    """This data class represents the output of a command."""

    command: str
    observation: str = ObservationType.RUN
    # Additional metadata captured from PS1
    metadata: CmdOutputMetadata = field(default_factory=CmdOutputMetadata)
    # Whether the command output should be hidden from the user
    hidden: bool = False

    def __init__(
        self,
        content: str,
        command: str,
        observation: str = ObservationType.RUN,
        metadata: dict | CmdOutputMetadata | None = None,
        hidden: bool = False,
        **kwargs,
    ):
        super().__init__(content)
        self.command = command
        self.observation = observation
        self.hidden = hidden
        if isinstance(metadata, dict):
            self.metadata = CmdOutputMetadata(**metadata)
        else:
            self.metadata = metadata or CmdOutputMetadata()

        # Handle legacy attribute
        if 'exit_code' in kwargs:
            self.metadata.exit_code = kwargs['exit_code']
        if 'command_id' in kwargs:
            self.metadata.pid = kwargs['command_id']

    @property
    def command_id(self) -> int:
        return self.metadata.pid

    @property
    def exit_code(self) -> int:
        return self.metadata.exit_code

    @property
    def error(self) -> bool:
        return self.exit_code != 0

    @property
    def message(self) -> str:
        return f'Command `{self.command}` executed with exit code {self.exit_code}.'

    @property
    def success(self) -> bool:
        return not self.error

    def __str__(self) -> str:
        return (
            f'**CmdOutputObservation (source={self.source}, exit code={self.exit_code}, '
            f'metadata={json.dumps(self.metadata.model_dump(), indent=2)})**\n'
            '--BEGIN AGENT OBSERVATION--\n'
            f'{self.to_agent_observation()}\n'
            '--END AGENT OBSERVATION--'
        )

    def to_agent_observation(self) -> str:
        ret = f'{self.metadata.prefix}{self.content}{self.metadata.suffix}'
        if self.metadata.working_dir:
            ret += f'\n[Current working directory: {self.metadata.working_dir}]'
        if self.metadata.py_interpreter_path:
            ret += f'\n[Python interpreter: {self.metadata.py_interpreter_path}]'
        if self.metadata.exit_code != -1:
            ret += f'\n[Command finished with exit code {self.metadata.exit_code}]'
        return ret


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

    @property
    def success(self) -> bool:
        return True  # IPython cells are always considered successful

    def __str__(self) -> str:
        return f'**IPythonRunCellObservation**\n{self.content}'
