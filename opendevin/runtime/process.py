from abc import ABC, abstractmethod
from typing import Generator


class Process(ABC):
    @property
    @abstractmethod
    def pid(self) -> int:
        pass

    @property
    @abstractmethod
    def command(self) -> str:
        pass

    @abstractmethod
    def read_logs(self) -> str:
        pass

    @abstractmethod
    def stream_logs(self) -> Generator[str, None, None]:
        pass
