from abc import ABC, abstractmethod


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
