from opendevin.core.config import config

from .files import FileStore
from .local import LocalFileStore
from .memory import InMemoryFileStore
from .s3 import S3FileStore


def _get_file_store() -> FileStore:
    if config.file_store == 'local':
        return LocalFileStore(config.file_store_path)
    elif config.file_store == 's3':
        return S3FileStore()
    return InMemoryFileStore()


singleton = _get_file_store()


def get_file_store() -> FileStore:
    return singleton
