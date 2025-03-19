from dataclasses import dataclass


@dataclass
class CommandResult:
    content: str
    exit_code: int
    command: str
    working_dir: str
