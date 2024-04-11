import os

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


def validate_file_content(file_path: str, content: str) -> str:
    """
    Validates the content of a code file by checking for syntax errors.

    Args:
        file_path (str): The full path to the file being validated.
        content (str): The content of the file to be validated.

    Returns:
        str or None: Error message if there are syntax errors, otherwise None.
    """

    _, extension = os.path.splitext(file_path)
    extension = extension.lstrip('.')

    if extension == 'py':
        return _validate_python(content)
    elif extension == 'js':
        return _validate_javascript(content)
    elif extension == 'cpp' or extension == 'cc' or extension == 'cxx':
        return _validate_cpp(content)
    elif extension == 'java':
        return _validate_java(content)
    else:
        return f'Unsupported file type: {extension}'


def _validate_python(content: str) -> str:
    # cmd = f'python -c "{content}"'
    # result = CmdRunAction(cmd).run( )
    # if result.exit_code != 0:
    #    return result.stderr
    return ''


def _validate_javascript(content: str) -> str:
    # cmd = f'node -e "{content}"'
    # result = CmdRunAction(cmd).run(AgentController())
    # if result.exit_code != 0:
    #    return result.stderr
    return ''


def _validate_cpp(content: str) -> str:
    # with open('temp.cpp', 'w') as f:
    #    f.write(content)
    # cmd = 'g++ -Wall -Wextra -std=c++11 -o temp temp.cpp'
    # result = CmdRunAction(cmd).run(AgentController())
    # if result.exit_code != 0:
    #    return result.stderr
    # os.remove('temp.cpp')
    # os.remove('temp')
    return ''


def _validate_java(content: str) -> str:
    # with open('temp.java', 'w') as f:
    #    f.write(content)
    # cmd = 'javac temp.java'
    # result = CmdRunAction(cmd).run(AgentController())
    # if result.exit_code != 0:
    #    return result.stderr
    # os.remove('temp.java')
    return ''


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
            all_lines = file.readlines()  # this can not happen in mode w
            insert = self.content.split('\n')
            new_file = all_lines[:self.start] if self.start != 0 else ['']
            new_file += insert + [''] if self.end == - \
                1 else all_lines[self.end:]
            content_str = '\n'.join(new_file)
            validation_error = validate_file_content(whole_path, content_str)
            if not validation_error:
                file.write(content_str)
                return FileWriteObservation(content='', path=self.path)
            else:
                # Revert to the old file content
                file.write('\n'.join(all_lines))
                return AgentErrorObservation(content=validation_error)

    @property
    def message(self) -> str:
        return f'Writing file: {self.path}'
