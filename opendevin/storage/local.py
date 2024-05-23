import os

from .files import FileStore


class LocalFileStore(FileStore):
    root: str

    def __init__(self, root: str):
        self.root = root
        os.makedirs(self.root, exist_ok=True)

    def get_full_path(self, path: str) -> str:
        if path.startswith('/'):
            path = path[1:]
        return os.path.join(self.root, path)

    def write(self, path: str, contents: str) -> None:
        full_path = self.get_full_path(path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, 'w') as f:
            f.write(contents)

    def read(self, path: str) -> str:
        full_path = self.get_full_path(path)
        with open(full_path, 'r') as f:
            return f.read()

    def list(self, path: str) -> list[str]:
        full_path = self.get_full_path(path)
        files = [os.path.join(path, f) for f in os.listdir(full_path)]
        files = [f + '/' if os.path.isdir(self.get_full_path(f)) else f for f in files]
        return files

    def delete(self, path: str) -> None:
        full_path = self.get_full_path(path)
        os.remove(full_path)
