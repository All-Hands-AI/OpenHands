import os
from dataclasses import dataclass

from opendevin.observation import FileReadObservation, FileWriteObservation
from opendevin.schema import ActionType

from .base import ExecutableAction

# This is the path where the workspace is mounted in the container
# The LLM sometimes returns paths with this prefix, so we need to remove it
PATH_PREFIX = '/workspace/'


def resolve_path(base_path, file_path):
    if file_path.startswith(PATH_PREFIX):
        file_path = file_path[len(PATH_PREFIX):]
    return os.path.join(base_path, file_path)

# TODO: need to add start_line and end_line here


@dataclass
class FileReadAction(ExecutableAction):
    path: str
    action: str = ActionType.READ

    def run(self, controller) -> FileReadObservation:
        path = resolve_path(controller.workdir, self.path)
        with open(path, 'r', encoding='utf-8') as file:
            return FileReadObservation(path=path, content=file.read())

    @property
    def message(self) -> str:
        return f'Reading file: {self.path}'

# TODO: need to add start_line and end_line here


@dataclass
class FileWriteAction(ExecutableAction):
    path: str
    content: str
    action: str = ActionType.WRITE

    def run(self, controller) -> FileWriteObservation:
        whole_path = resolve_path(controller.workdir, self.path)
        # TODO: Add temp file to revert back to if code build fails
        with open(whole_path, 'w', encoding='utf-8') as file:
            file.write(self.content)

        # TODO: Check the new file to see if the code was written properly
        return FileWriteObservation(content='', path=self.path)

    @property
    def message(self) -> str:
        return f'Writing file: {self.path}'
