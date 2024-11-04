import os
import shutil
from functools import wraps
from openhands.core.logger import openhands_logger as logger
from openhands.storage.files import FileStore


def local_operation(func):
    @wraps(func)
    def wrapper(self, path: str, *args, **kwargs):
        try:
            return func(self, path, *args, **kwargs)
        except Exception as e:
            operation = func.__name__
            logger.error(f'Error during local file {operation}: {str(e)}')
            raise FileNotFoundError(f'Failed to {operation} local {"file" if operation != "list" else "files"} at path {path}: {e}')
    return wrapper


class LocalFileStore(FileStore):
    root: str

    def __init__(self, root: str):
        self.root = root
        os.makedirs(self.root, exist_ok=True)

    def get_full_path(self, path: str) -> str:
        if path.startswith('/'):
            path = path[1:]
        return os.path.join(self.root, path)

    @local_operation
    def write(self, path: str, contents: str | bytes):
        full_path = self.get_full_path(path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        mode = 'w' if isinstance(contents, str) else 'wb'
        with open(full_path, mode) as f:
            f.write(contents)

    @local_operation
    def read(self, path: str) -> str:
        full_path = self.get_full_path(path)
        with open(full_path, 'r') as f:
            return f.read()

    @local_operation
    def list(self, path: str) -> list[str]:
        full_path = self.get_full_path(path)
        files = [os.path.join(path, f) for f in os.listdir(full_path)]
        files = [f + '/' if os.path.isdir(self.get_full_path(f)) else f for f in files]
        return files

    @local_operation
    def delete(self, path: str) -> None:
        full_path = self.get_full_path(path)
        if not os.path.exists(full_path):
            logger.debug(f'Local path does not exist: {full_path}')
            return
        if os.path.isfile(full_path):
            os.remove(full_path)
            logger.debug(f'Removed local file: {full_path}')
        elif os.path.isdir(full_path):
            shutil.rmtree(full_path)
            logger.debug(f'Removed local directory: {full_path}')

