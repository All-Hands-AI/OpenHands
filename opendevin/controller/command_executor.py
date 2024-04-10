from abc import ABC, abstractmethod
from typing import Any


class CommandExecutor(ABC):
    @abstractmethod
    def execute(self, cmd: str) -> tuple[int, str]:
        pass

    @abstractmethod
    def execute_in_background(self, cmd: str) -> Any:
        pass

    @abstractmethod
    def kill_background(self, id: int) -> Any:
        pass

    @abstractmethod
    def read_logs(self, id: int) -> str:
        pass

    @abstractmethod
    def close(self) -> None:
        pass
