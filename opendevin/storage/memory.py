from .files import FileStore


class InMemoryFileStore(FileStore):
    files: dict[str, str] = {}

    def write(self, path: str, contents: str) -> None:
        self.files[path] = contents

    def read(self, path: str) -> str:
        if path not in self.files:
            raise FileNotFoundError(path)
        return self.files[path]

    def list(self, path: str) -> list[str]:
        depth = path.count('/')
        files = []
        for file in self.files:
            if not file.startswith(path):
                continue
            if file.count('/') != depth:
                continue
            files.append(file)
        return files

    def delete(self, path: str) -> None:
        del self.files[path]
