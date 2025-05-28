import httpx
import tenacity

from openhands.storage.files import FileStore
from openhands.utils.async_utils import EXECUTOR, call_async_from_sync


class WebHookFileStore(FileStore):
    """
    File store which includea a web hook to be invoked after any changes occur.
    """
    file_store: FileStore
    base_url: str
    client: httpx.Client

    def __init__(self, file_store: FileStore, base_url: str, client: httpx.Client | None):
        self.file_store = file_store
        self.base_url = base_url
        if client is None:
            client = httpx.Client()
        self.client = client

    def write(self, path: str, contents: str | bytes) -> None:
        self.file_store.write(path, contents)
        EXECUTOR.submit(self._on_write, path, contents)
        self._on_write(path, contents)

    def read(self, path: str) -> str:
        return self.file_store.read(path)

    def list(self, path: str) -> list[str]:
        self.file_store.list(path)

    def delete(self, path: str) -> None:
        self.file_store.delete(path)
        EXECUTOR.submit(self._on_delete, path)

    @tenacity.retry(
        wait=tenacity.wait_fixed(1),
        stop=tenacity.stop_after_attempt(3),
    )
    def _on_write(self, path: str, contents: str | bytes) -> None:
        base_url = self.url + path
        response = self.client.post(base_url, content=contents)
        response.raise_for_status()

    @tenacity.retry(
        wait=tenacity.wait_fixed(1),
        stop=tenacity.stop_after_attempt(3),
    )
    def _on_delete(self, path: str) -> None:
        base_url = self.url + path
        response = self.client.delete(base_url)
        response.raise_for_status()
