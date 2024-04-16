import os

from dataclasses import dataclass

from opendevin.observation import (
    FileReadObservation,
    FileWriteObservation,
    Observation
)

from opendevin.schema import ActionType

from .base import ExecutableAction

# This is the path where the workspace is mounted in the container
# The LLM sometimes returns paths with this prefix, so we need to remove it
PATH_PREFIX = '/workspace/'


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
    thoughts: str = ''
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
            code_view = ''.join(code_slice)
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

    def run(self, controller) -> Observation:
        whole_path = resolve_path(controller.workdir, self.path)
        mode = 'w' if not os.path.exists(whole_path) else 'r+'
        insert = self.content.split('\n')
        with open(whole_path, mode, encoding='utf-8') as file:
            if mode != 'w':
                all_lines = file.readlines()
                new_file = [''] if self.start == 0 else all_lines[:self.start]
                new_file += [i + '\n' for i in insert]
                new_file += [''] if self.end == -1 else all_lines[self.end:]
            else:
                new_file = insert

            file.seek(0)
            file.writelines(new_file)
            file.truncate()
            return FileWriteObservation(content=''.join(new_file), path=self.path)

    @property
    def message(self) -> str:
        return f'Writing file: {self.path}'
