from .files import FileStore
from .local import LocalFileStore
from .memory import InMemoryFileStore
from .s3 import S3FileStore


def get_file_store(file_store: str, file_store_path: str | None = None) -> FileStore:
    if file_store == 'local':
        if file_store_path is None:
            raise ValueError('file_store_path is required for local file store')
        return LocalFileStore(file_store_path)
    elif file_store == 's3':
        return S3FileStore()
    return InMemoryFileStore()
