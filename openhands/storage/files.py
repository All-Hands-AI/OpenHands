from abc import abstractmethod


class FileStore:
    @abstractmethod
    def write(self, path: str, contents: str | bytes) -> None:
        pass

    @abstractmethod
    def read(self, path: str) -> str:
        pass

    @abstractmethod
    def list(self, path: str) -> list[str]:
        pass

    @abstractmethod
    def delete(self, path: str) -> None:
        pass
