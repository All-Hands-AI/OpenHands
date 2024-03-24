import os
from dataclasses import dataclass

from opendevin.observation import Observation
from .base import ExecutableAction

@dataclass
class FileReadAction(ExecutableAction):
    path: str
    workspace_dir: str = ""  # TODO: maybe handle this in a more elegant way

    def run(self, *args, **kwargs) -> Observation:
        # remove the leading /workspace/ from the path (inside container)
        path = os.path.join(self.workspace_dir, self.path.lstrip("/workspace/"))
        with open(path, 'r') as file:
            return Observation(file.read())

@dataclass
class FileWriteAction(ExecutableAction):
    path: str
    contents: str
    workspace_dir: str = ""

    def run(self, *args, **kwargs) -> Observation:
        path = os.path.join(self.workspace_dir, self.path.lstrip("/workspace/"))
        with open(path, 'w') as file:
            file.write(self.contents)
        return Observation(f"File written to {path}")
