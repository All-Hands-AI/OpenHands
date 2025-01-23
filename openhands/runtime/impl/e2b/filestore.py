from openhands.storage.files import FileStore


class E2BFileStore(FileStore):
    def __init__(self, filesystem):
        self.filesystem = filesystem

    def write(self, path: str, contents: str | bytes) -> None:
        self.filesystem.write(path, contents)

    def read(self, path: str) -> str:
        return self.filesystem.read(path)

    def list(self, path: str) -> list[str]:
        return self.filesystem.list(path)

    def delete(self, path: str) -> None:
        self.filesystem.delete(path)
