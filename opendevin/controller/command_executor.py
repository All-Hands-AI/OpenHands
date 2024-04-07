from typing import Tuple
from abc import ABC, abstractmethod


class CommandExecutor(ABC):
    @abstractmethod
    def execute(self, cmd: str) -> Tuple[int, str]:
        pass

    @abstractmethod
    def execute_in_background(self, cmd: str):
        pass

    @abstractmethod
    def kill_background(self, id: int):
        pass

    @abstractmethod
    def read_logs(self, id: int) -> str:
        pass

    @abstractmethod
    def close(self):
        pass
