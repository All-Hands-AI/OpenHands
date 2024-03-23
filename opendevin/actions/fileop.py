import os
from dataclasses import dataclass

from .base import Action


@dataclass
class FileReadAction(Action):
    base_path: str
    file_path: str

    def run(self, *args, **kwargs) -> str:
        file_path = os.path.join(self.base_path, self.file_path)
        with open(file_path, 'r') as file:
            return file.read()

@dataclass
class FileWriteAction(Action):
    base_path: str
    file_path: str
    contents: str

    def run(self, *args, **kwargs) -> str:
        file_path = os.path.join(self.base_path, self.file_path)
        with open(file_path, 'w') as file:
            file.write(self.contents)
        return ""
