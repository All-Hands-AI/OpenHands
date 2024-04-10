import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

from dataclasses import dataclass

from opendevin.observation import (
    FileReadObservation,
    FileWriteObservation,
    AgentErrorObservation,
    Observation
)

from opendevin.schema import ActionType

from .base import ExecutableAction

# This is the path where the workspace is mounted in the container
# The LLM sometimes returns paths with this prefix, so we need to remove it
PATH_PREFIX = '/workspace/'


def validate_file_content(file_path: str, content: str) -> Optional[str]:
    """
    Validates the content of a code file by checking for syntax errors.

    Args:
        file_path (str): The full path to the file being validated.
        content (str): The content of the file to be validated.

    Returns:
        str or None: Error message if there are syntax errors, otherwise None.
    """
    file_extension = os.path.splitext(
        file_path)[1][1:]  # Get the file extension without the dot

    # Determine the appropriate validation command based on the file extension
    validation_commands = {
        'py': [sys.executable, '-c', 'import sys; compile(sys.stdin.read(), "<string>", "exec")'],
        'js': ['node', '-c', '-'],
        'java': ['javac', '-encoding', 'UTF-8', '-Xlint:all', '-'],
        'cpp': ['g++', '-std=c++11', '-Wall', '-Wextra', '-Werror', '-x', 'c++', '-c', '-'],
        'c': ['gcc', '-std=c11', '-Wall', '-Wextra', '-Werror', '-x', 'c', '-c', '-']
    }
    ignore_types = ['txt', 'md', 'doc', 'pdf']

    if file_extension in ignore_types:
        return None

    elif file_extension in validation_commands:
        try:
            # Run the validation command and capture the output
            subprocess.run(
                validation_commands[file_extension],
                input=content.encode(),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True, check=True
            )
        except subprocess.CalledProcessError as e:
            return e.stderr.strip()
        else:
            return None
    else:
        # If the file extension is not recognized, return a default error message
        return f'Unsupported file type: {file_extension}'


def resolve_path(base_path: str, file_path: str) -> str:
    if file_path.startswith(PATH_PREFIX):
        file_path = file_path[len(PATH_PREFIX):]
    return os.path.join(base_path, file_path)


@dataclass
class FileReadAction(ExecutableAction):
    """
    Reads a file from a given path up to 100 lines.
    Default lines 0:100
    """
    path: str
    start_index: int = 0
    max_lines: int = 100
    action: str = ActionType.READ

    # def run(self, controller) -> FileReadObservation:
    #     path = resolve_path(controller.workdir, self.path)
    def run(self):
        path = resolve_path('./workspace', self.path)
        if not os.path.exists(path):
            return FileReadObservation(path=path, content='File not found')

        try:
            all_lines = []
            with open(path, 'r', encoding='utf-8') as file:
                for line in file:
                    all_lines.append(line.strip('\n'))
                total_lines = len(all_lines)
                if total_lines >= self.max_lines:
                    end_index = self.start_index + self.max_lines - 1 if total_lines - \
                        self.start_index - self.max_lines >= 0 else -1
                    code_slice = all_lines[self.start_index - 1: end_index]
                else:
                    code_slice = all_lines[:]
                code_view = '\n'.join(code_slice)
        except (IOError, UnicodeDecodeError) as e:
            return FileReadObservation(path=path, content=f'Error reading file: {e}')

        return FileReadObservation(path=path, content=code_view)

    @property
    def message(self) -> str:
        return f'Reading file: {self.path}'


@dataclass
class FileWriteAction(ExecutableAction):
    path: str
    content: str
    start: int
    end: int
    action: str = ActionType.WRITE

    def run(self, controller) -> Observation:
        full_path = resolve_path(controller.workdir, self.path)
        parent_dir = os.path.dirname(full_path)
        Path(parent_dir).mkdir(parents=True, exist_ok=True)

        all_lines = []
        try:
            with open(full_path, 'r', encoding='utf-8') as file:
                for line in file:
                    all_lines.append(line.strip('\n'))
        except (IOError, UnicodeDecodeError):
            all_lines = []

        # Split the content into lines
        new_lines = self.content.split('\n')

        # Check if the start and end indices are valid
        if self.start < 0 or self.end < 0:
            return AgentErrorObservation(content=f'Invalid start or end index: {self.start}, {self.end}')
        elif self.start <= len(all_lines) and self.start + len(new_lines) <= len(all_lines):
            new_file_lines = all_lines[:self.start-1] + \
                new_lines + all_lines[len(all_lines)-1:]
        elif self.start <= len(all_lines) and self.start + len(new_lines) > len(all_lines):
            new_file_lines = all_lines[:self.start-1] + new_lines
        elif self.start > len(all_lines):
            new_file_lines = all_lines + \
                ['' for i in range(len(all_lines), self.start-1)] + new_lines

        new_file_content = '\n'.join(new_file_lines)

        validation_status = validate_file_content(full_path, new_file_content)

        if not validation_status:
            try:
                with open(full_path, 'w', encoding='utf-8') as file:
                    file.write(new_file_content)
            except IOError as e:
                return AgentErrorObservation(content=f'Error writing file: {e}')
            return FileWriteObservation(content=self.content, path=self.path)
        else:
            return AgentErrorObservation(content=validation_status)

    @property
    def message(self) -> str:
        return f'Writing file: {self.path}'
