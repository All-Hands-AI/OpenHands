import os
from dataclasses import dataclass

from opendevin.observation import FileReadObservation, FileWriteObservation
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
    path: str
    action: str = ActionType.READ

    async def run(self, controller) -> FileReadObservation:
        path = resolve_path(self.path)
        with open(path, 'r', encoding='utf-8') as file:
            return FileReadObservation(path=path, content=file.read())

    @property
    def message(self) -> str:
        return f'Reading file: {self.path}'


@dataclass
class FileWriteAction(ExecutableAction):
    path: str
    content: str
    action: str = ActionType.WRITE

    async def run(self, controller) -> FileWriteObservation:
        whole_path = resolve_path(self.path)
        with open(whole_path, 'w', encoding='utf-8') as file:
            file.write(self.content)
        return FileWriteObservation(content='', path=self.path)

    @property
    def message(self) -> str:
        return f'Writing file: {self.path}'
