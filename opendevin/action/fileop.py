import os

from dataclasses import dataclass
from pathlib import Path

from opendevin.observation import (
    Observation,
    FileReadObservation,
    FileWriteObservation,
    AgentErrorObservation,
)

from opendevin.schema import ActionType
from opendevin.sandbox import E2BBox
from opendevin import config

from .base import ExecutableAction

SANDBOX_PATH_PREFIX = '/workspace/'


def resolve_path(file_path):
    # Sanitize the path with respect to the root of the full sandbox
    # (deny any .. path traversal to parent directories of this)
    abs_path_in_sandbox = (Path(SANDBOX_PATH_PREFIX) / Path(file_path)).resolve()

    # If the path is outside the workspace, deny it
    if not abs_path_in_sandbox.is_relative_to(SANDBOX_PATH_PREFIX):
        raise PermissionError(f'File access not permitted: {file_path}')

    # Get path relative to the root of the workspace inside the sandbox
    path_in_workspace = abs_path_in_sandbox.relative_to(Path(SANDBOX_PATH_PREFIX))

    # Get path relative to host
    path_in_host_workspace = Path(config.get('WORKSPACE_BASE')) / path_in_workspace

    return path_in_host_workspace


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

    async def run(self, controller) -> Observation:
        if isinstance(controller.action_manager.sandbox, E2BBox):
            content = controller.action_manager.sandbox.filesystem.read(
                self.path)
            read_lines = self._read_lines(content.split('\n'))
            code_view = ''.join(read_lines)
        else:
            try:
                whole_path = resolve_path(self.path)
                self.start = max(self.start, 0)
                try:
                    with open(whole_path, 'r', encoding='utf-8') as file:
                        read_lines = self._read_lines(file.readlines())
                        code_view = ''.join(read_lines)
                except FileNotFoundError:
                    return AgentErrorObservation(f'File not found: {self.path}')
                except IsADirectoryError:
                    return AgentErrorObservation(f'Path is a directory: {self.path}. You can only read files')
            except PermissionError:
                return AgentErrorObservation(f'Malformed paths not permitted: {self.path}')
        return FileReadObservation(path=self.path, content=code_view)

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
        Insert the new content to the original content based on self.start and self.end
        """
        new_lines = [''] if self.start == 0 else original[:self.start]
        new_lines += [i + '\n' for i in to_insert]
        new_lines += [''] if self.end == -1 else original[self.end:]
        return new_lines

    async def run(self, controller) -> Observation:
        insert = self.content.split('\n')

        if isinstance(controller.action_manager.sandbox, E2BBox):
            files = controller.action_manager.sandbox.filesystem.list(self.path)
            if self.path in files:
                all_lines = controller.action_manager.sandbox.filesystem.read(self.path)
                new_file = self._insert_lines(self.content.split('\n'), all_lines)
                controller.action_manager.sandbox.filesystem.write(self.path, ''.join(new_file))
            else:
                return AgentErrorObservation(f'File not found: {self.path}')
        else:
            try:
                whole_path = resolve_path(self.path)
                mode = 'w' if not os.path.exists(whole_path) else 'r+'
                try:
                    with open(whole_path, mode, encoding='utf-8') as file:
                        if mode != 'w':
                            all_lines = file.readlines()
                            new_file = self._insert_lines(insert, all_lines)
                        else:
                            new_file = [i + '\n' for i in insert]

                        file.seek(0)
                        file.writelines(new_file)
                        file.truncate()
                except FileNotFoundError:
                    return AgentErrorObservation(f'File not found: {self.path}')
                except IsADirectoryError:
                    return AgentErrorObservation(f'Path is a directory: {self.path}. You can only write to files')
            except PermissionError:
                return AgentErrorObservation(f'Malformed paths not permitted: {self.path}')
        return FileWriteObservation(content='', path=self.path)

    @property
    def message(self) -> str:
        return f'Writing file: {self.path}'
