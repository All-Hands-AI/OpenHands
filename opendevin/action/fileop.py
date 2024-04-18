import os

from dataclasses import dataclass

from opendevin.observation import (
    FileReadObservation,
    FileWriteObservation
)

from opendevin.schema import ActionType
from opendevin.sandbox import E2BBox
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

    def _read_lines(self, all_lines: list[str]):
        if self.end == -1:
            if self.start == 0:
                return all_lines
            else:
                return all_lines[self.start:]
        else:
            num_lines = len(all_lines)
            begin = max(0, min(self.start, num_lines - 2))
            end = -1 if self.end > num_lines else max(begin + 1, self.end)
            return all_lines[begin:end]

    async def run(self, controller) -> FileReadObservation:
        code_view: str
        if isinstance(controller.command_manager.sandbox, E2BBox):
            content = controller.command_manager.sandbox.filesystem.read(
                self.path)
            read_lines = self._read_lines(content.split('\n'))
            code_view = ''.join(read_lines)
        else:
            path = resolve_path(self.path)
            self.start = max(self.start, 0)
            with open(path, 'r', encoding='utf-8') as file:
                read_lines = self._read_lines(file.readlines())
                code_view = ''.join(read_lines)
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

    def _insert_lines(self, to_insert: list[str], original: list[str]):
        """
        Insert the new conent to the original content based on self.start and self.end
        """
        new_lines = [''] if self.start == 0 else original[:self.start]
        new_lines += [i + '\n' for i in to_insert]
        new_lines += [''] if self.end == -1 else original[self.end:]
        return new_lines

    async def run(self, controller) -> FileWriteObservation:
        obs = f'WRITE OPERATION:\nYou have written to "{self.path}" on these lines: {self.start}:{self.end}.'
        insert = self.content.split('\n')
        new_file: list[str]

        if isinstance(controller.command_manager.sandbox, E2BBox):
            files = controller.command_manager.sandbox.filesystem.list(self.path)
            if self.path in files:
                all_lines = controller.command_manager.sandbox.filesystem.read(self.path)
                new_file = self._insert_lines(self.content.split('\n'), all_lines)
                controller.command_manager.sandbox.filesystem.write(self.path, ''.join(new_file))
            else:
                new_file = insert
                controller.command_manager.sandbox.filesystem.write(self.path, ''.join(new_file))
        else:
            whole_path = resolve_path(self.path)
            mode = 'w' if not os.path.exists(whole_path) else 'r+'
            with open(whole_path, mode, encoding='utf-8') as file:
                if mode != 'w':
                    all_lines = file.readlines()
                    new_file = self._insert_lines(insert, all_lines)
                else:
                    new_file = insert

                file.seek(0)
                file.writelines(new_file)
                file.truncate()

        return FileWriteObservation(content=obs + ''.join(new_file), path=self.path)

    @property
    def message(self) -> str:
        return f'Writing file: {self.path}'
