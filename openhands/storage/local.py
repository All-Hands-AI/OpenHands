import os
import shutil
from pathlib import Path

from openhands.core.logger import openhands_logger as logger
from openhands.storage.files import FileStore


class LocalFileStore(FileStore):
    """Stores files in the local filesystem"""

    def __init__(self, base_path: str | Path):
        if isinstance(base_path, str):
            base_path = Path(base_path)
        self.base_path: Path = base_path
        if not self.base_path.exists():
            self.base_path.mkdir(parents=True, exist_ok=True)

    def get_full_path(self, path: str) -> Path:
        """Returns the full absolute path for a given relative path."""
        if path.startswith('/'):
             # If path is already absolute, use it directly (maybe warn?)
             logger.warning(f"Received absolute path '{path}', using it directly.")
             return Path(path)
        full_path = self.base_path.joinpath(path).resolve()
        # Basic check to prevent escaping the base path
        if self.base_path not in full_path.parents:
             # Or check full_path.is_relative_to(self.base_path) in Python 3.9+
             raise PermissionError(f"Attempted to access path '{path}' outside base directory '{self.base_path}'")
        return full_path

    def write(self, path: str, contents: str | bytes, append=False) -> None:
        full_path = self.get_full_path(path)
        logger.debug(f'Writing to file {full_path}')
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        mode = 'a' if append else 'w'
        if isinstance(contents, bytes):
            mode += 'b'
        with open(full_path, mode) as f:
            f.write(contents)

    def read(self, path: str) -> str:
        full_path = self.get_full_path(path)
        logger.debug(f'Reading from file {full_path}')
        with open(full_path, 'r') as f:
            return f.read()

    def list(self, path: str) -> list[str]:
        full_path = self.get_full_path(path)
        logger.debug(f'Listing files in {full_path}')
        if not full_path.is_dir():
             raise FileNotFoundError(f"Directory not found: {full_path}")
        return [str(p.relative_to(self.base_path)) for p in full_path.iterdir()]

    def delete(self, path: str) -> None:
        full_path = self.get_full_path(path)
        logger.debug(f'Deleting {full_path}')
        if full_path.is_dir():
            shutil.rmtree(full_path)
        elif full_path.is_file():
            os.remove(full_path)
        else:
            # Path doesn't exist, treat as success (idempotent delete)
            logger.debug(f'Path {full_path} not found, skipping delete.')
