import os
from dataclasses import dataclass

from .base import ExecutableAction


@dataclass
class FileReadAction(ExecutableAction):
    path: str

    def run(self, *args, **kwargs) -> str:
        with open(self.path, 'r') as file:
            return file.read()

@dataclass
class FileWriteAction(ExecutableAction):
    path: str
    contents: str

    def run(self, *args, **kwargs) -> str:
        with open(self.path, 'w') as file:
            file.write(self.contents)
        return ""
