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
            return FileReadObservation(path=path, content='\n'.join(code_slice))

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

    def run(self, controller) -> FileWriteObservation:
        whole_path = resolve_path(controller.workdir, self.path)

        with open(whole_path, 'w', encoding='utf-8') as file:
            all_lines = file.readlines()
            insert = self.content.split('\n')
            new_file = all_lines[:self.start] + insert + all_lines[self.end:]
            # if valid_changes(new_file, self.path):
            #    file.write('\n'.join(new_file))
            file.write('\n'.join(new_file))
        # TODO: Check the new file to see if the code was written properly
        return FileWriteObservation(content='', path=self.path)

    @property
    def message(self) -> str:
        return f'Writing file: {self.path}'
