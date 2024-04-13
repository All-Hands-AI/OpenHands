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

    # @property
    # @abstractmethod
    # def exit_code(self) -> int | None: # The reason it can be none is because the process can still be running
    #    pass

    # @abstractmethod
    # def kill(self):
    #     pass

    @abstractmethod
    def read_logs(self) -> str:
        pass
