import os
from functools import wraps
from openhands.core.logger import openhands_logger as logger
from openhands.storage.files import FileStore


def memory_operation(func):
    @wraps(func)
    def wrapper(self, path: str, *args, **kwargs):
        try:
            return func(self, path, *args, **kwargs)
        except Exception as e:
            operation = func.__name__
            logger.error(f'Error during in-memory {operation}: {str(e)}')
            raise FileNotFoundError(f'Failed to {operation} in-memory {"file" if operation != "list" else "files"} at path {path}: {e}')
    return wrapper


class InMemoryFileStore(FileStore):
    files: dict[str, str]

    def __init__(self):
        self.files = {}

    @memory_operation
    def write(self, path: str, contents: str) -> None:
        self.files[path] = contents

    @memory_operation
    def read(self, path: str) -> str:
        if path not in self.files:
            raise FileNotFoundError(path)
        return self.files[path]

    @memory_operation
    def list(self, path: str) -> list[str]:
        files = []
        for file in self.files:
            if not file.startswith(path):
                continue
            suffix = file.removeprefix(path)
            parts = suffix.split('/')
            if parts[0] == '':
                parts.pop(0)
            if len(parts) == 1:
                files.append(file)
            else:
                dir_path = os.path.join(path, parts[0])
                if not dir_path.endswith('/'):
                    dir_path += '/'
                if dir_path not in files:
                    files.append(dir_path)
        return files

    @memory_operation
    def delete(self, path: str) -> None:
        keys_to_delete = [key for key in self.files.keys() if key.startswith(path)]
        for key in keys_to_delete:
            del self.files[key]
        logger.debug(f'Cleared in-memory file store: {path}')

