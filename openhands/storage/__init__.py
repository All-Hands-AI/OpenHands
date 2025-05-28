import httpx
from openhands.storage.files import FileStore
from openhands.storage.google_cloud import GoogleCloudFileStore
from openhands.storage.local import LocalFileStore
from openhands.storage.memory import InMemoryFileStore
from openhands.storage.s3 import S3FileStore
from openhands.storage.web_hook import WebHookFileStore


def get_file_store(
    file_store: str,
    file_store_path: str | None = None,
    file_store_web_hook_url: str | None = None,
    file_store_web_hook_headers: dict | None = None,
) -> FileStore:
    if file_store == 'local':
        if file_store_path is None:
            raise ValueError('file_store_path is required for local file store')
        file_store = LocalFileStore(file_store_path)
    elif file_store == 's3':
        file_store = S3FileStore(file_store_path)
    elif file_store == 'google_cloud':
        file_store = GoogleCloudFileStore(file_store_path)
    else:
        file_store = InMemoryFileStore()
    if file_store_web_hook_url:
        file_store = WebHookFileStore(
            file_store,
            file_store_web_hook_url,
            httpx.Client(headers=file_store_web_hook_headers or {})
        )
    return file_store
