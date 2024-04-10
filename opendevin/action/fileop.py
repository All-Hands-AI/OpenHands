import os
import subprocess
import sys

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

# claude generated this and I have no clue if it works properly


def validate_file_content(file_path, content):
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
        return ''

    elif file_extension in validation_commands:
        try:
            # Run the validation command and capture the output
            subprocess.run(
                validation_commands[file_extension],
                input=content.encode('utf-8'),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True, check=True
            )
        except subprocess.CalledProcessError as e:
            return e.stderr.strip()
        else:
            return ''
    else:
        # If the file extension is not recognized, return a default error message
        return f'Unsupported file type: {file_extension}'


def resolve_path(base_path, file_path):
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
    action: str = ActionType.READ

    def run(self, controller) -> FileReadObservation:
        path = resolve_path(controller.workdir, self.path)
        with open(path, 'r', encoding='utf-8') as file:
            all_lines = file.readlines()
            total_lines = len(all_lines)
            if total_lines >= 100:
                end_index = self.start_index + 100 if total_lines - \
                    self.start_index - 100 >= 0 else -1
                code_slice = all_lines[self.start_index: end_index]
            else:
                code_slice = all_lines[:]
            if isinstance(code_slice, list) and len(code_slice) > 1:
                code_view = '\n'.join(code_slice)
            return FileReadObservation(path=path, content=code_view)

    @property
    def message(self) -> str:
        return f'Reading file: {self.path}'


@dataclass
class FileWriteAction(ExecutableAction):
    path: str
    content: str
    start: int = 0
    end: int = -1
    action: str = ActionType.WRITE

    def run(self, controller) -> Observation:
        whole_path = resolve_path(controller.workdir, self.path)
        mode = 'w' if not os.path.exists(whole_path) else 'r+'

        with open(whole_path, mode, encoding='utf-8') as file:
            all_lines = file.readlines()
            insert = self.content.split('\n')
            new_file = all_lines[:self.start] if self.start != 0 else ['']
            new_file += insert + [''] if self.end == - \
                1 else all_lines[self.end:]
            content_str = '\n'.join(new_file)
            validation_error = validate_file_content(whole_path, content_str)
            if validation_error:
                file.write(content_str)
                return FileWriteObservation(content='', path=self.path)
            else:
                # Revert to the old file content
                file.write('\n'.join(all_lines))
                return AgentErrorObservation(content=validation_error)

    @property
    def message(self) -> str:
        return f'Writing file: {self.path}'
