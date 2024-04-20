from abc import ABC, abstractmethod
from typing import Dict
from typing import Tuple

from opendevin.sandbox.process import Process


class Sandbox(ABC):
    background_commands: Dict[int, Process] = {}

    @abstractmethod
    def execute(self, cmd: str) -> Tuple[int, str]:
        pass

    @abstractmethod
    def execute_in_background(self, cmd: str) -> Process:
        pass

    @abstractmethod
    def kill_background(self, id: int) -> Process:
        pass

    @abstractmethod
    def read_logs(self, id: int) -> str:
        pass

    @abstractmethod
    def close(self):
        pass
