import os

from dataclasses import dataclass

from opendevin.observation import (
    FileReadObservation,
    FileWriteObservation
)

from opendevin.schema import ActionType
from opendevin import config

from .base import ExecutableAction

SANDBOX_PATH_PREFIX = '/workspace/'


def resolve_path(file_path):
    if file_path.startswith(SANDBOX_PATH_PREFIX):
        # Sometimes LLMs include the absolute path of the file inside the sandbox
        file_path = file_path[len(SANDBOX_PATH_PREFIX):]
    return os.path.join(config.get('WORKSPACE_BASE'), file_path)


@dataclass
class FileReadAction(ExecutableAction):
    """
    Reads a file from a given path.
    Can be set to read specific lines using start and end
    Default lines 0:-1 (whole file)
    """
    path: str
    start: int = 0
    end: int = -1
    thoughts: str = ''
    action: str = ActionType.READ

    async def run(self, controller) -> FileReadObservation:
        path = resolve_path(self.path)
        self.start = max(self.start, 0)
        try:
            with open(path, 'r', encoding='utf-8') as file:
                if self.end == -1:
                    if self.start == 0:
                        code_view = file.read()
                    else:
                        all_lines = file.readlines()
                        code_slice = all_lines[self.start:]
                        code_view = ''.join(code_slice)
                else:
                    all_lines = file.readlines()
                    num_lines = len(all_lines)
                    begin = max(0, min(self.start, num_lines - 2))
                    end = -1 if self.end > num_lines else max(begin + 1, self.end)
                    code_slice = all_lines[begin:end]
                    code_view = ''.join(code_slice)
        except FileNotFoundError:
            raise FileNotFoundError(f'File not found: {self.path}')
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
    thoughts: str = ''
    action: str = ActionType.WRITE

    async def run(self, controller) -> FileWriteObservation:
        whole_path = resolve_path(self.path)
        mode = 'w' if not os.path.exists(whole_path) else 'r+'
        insert = self.content.split('\n')
        try:
            with open(whole_path, mode, encoding='utf-8') as file:
                if mode != 'w':
                    all_lines = file.readlines()
                    new_file = [''] if self.start == 0 else all_lines[:self.start]
                    new_file += [i + '\n' for i in insert]
                    new_file += [''] if self.end == -1 else all_lines[self.end:]
                else:
                    new_file = [i + '\n' for i in insert]

                file.seek(0)
                file.writelines(new_file)
                file.truncate()
        except FileNotFoundError:
            raise FileNotFoundError(f'File not found: {self.path}')
        return FileWriteObservation(content=f'Wrote to the file {self.path}', path=self.path)

    @property
    def message(self) -> str:
        return f'Writing file: {self.path}'
