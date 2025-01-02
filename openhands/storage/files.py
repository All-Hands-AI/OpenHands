from abc import abstractmethod


class FileStore:
    @abstractmethod
    def get_full_path(self, path: str) -> str:
        """Get the full path for a given relative path.

        Args:
            path: The relative path.

        Returns:
            The full path.
        """
        pass

    @abstractmethod
    def write(self, path: str, contents: str) -> None:
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
