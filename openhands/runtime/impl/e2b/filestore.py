from typing import Protocol

from openhands.storage.files import FileStore


class SupportsFilesystemOperations(Protocol):
    def write(self, path: str, contents: str | bytes) -> None: ...
    def read(self, path: str) -> str: ...
    def list(self, path: str) -> list[str]: ...
    def delete(self, path: str) -> None: ...


class E2BFileStore(FileStore):
    def __init__(self, filesystem: SupportsFilesystemOperations) -> None:
        self.filesystem = filesystem

    def write(self, path: str, contents: str | bytes) -> None:
        self.filesystem.write(path, contents)

    def read(self, path: str) -> str:
        return self.filesystem.read(path)

    def list(self, path: str) -> list[str]:
        return self.filesystem.list(path)

    def delete(self, path: str) -> None:
        self.filesystem.delete(path)
