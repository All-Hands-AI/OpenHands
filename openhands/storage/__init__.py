import os
import warnings
from typing import Any, Optional

import httpx

from openhands.storage.files import FileStore
from openhands.storage.local import LocalFileStore
from openhands.storage.memory import InMemoryFileStore
from openhands.storage.web_hook import WebHookFileStore

# Import optional storage backends
S3FileStore: Optional[Any] = None
GoogleCloudFileStore: Optional[Any] = None

try:
    from openhands.storage.s3 import S3FileStore
except ImportError:
    warnings.warn(
        'S3FileStore could not be loaded due to missing dependencies. Install with \'pip install "openhands-ai[all]"\' to use this feature.',
        stacklevel=2,
    )

try:
    from openhands.storage.google_cloud import GoogleCloudFileStore
except ImportError:
    warnings.warn(
        'GoogleCloudFileStore could not be loaded due to missing dependencies. Install with \'pip install "openhands-ai[all]"\' to use this feature.',
        stacklevel=2,
    )


def get_file_store(
    file_store_type: str,
    file_store_path: str | None = None,
    file_store_web_hook_url: str | None = None,
    file_store_web_hook_headers: dict | None = None,
) -> FileStore:
    store: FileStore
    if file_store_type == 'local':
        if file_store_path is None:
            raise ValueError('file_store_path is required for local file store')
        store = LocalFileStore(file_store_path)
    elif file_store_type == 's3':
        if S3FileStore is None:
            raise ImportError(
                'S3FileStore is not available. Install with \'pip install "openhands-ai[all]"\' to use this feature.'
            )
        store = S3FileStore(file_store_path)
    elif file_store_type == 'google_cloud':
        if GoogleCloudFileStore is None:
            raise ImportError(
                'GoogleCloudFileStore is not available. Install with \'pip install "openhands-ai[all]"\' to use this feature.'
            )
        store = GoogleCloudFileStore(file_store_path)
    else:
        store = InMemoryFileStore()
    if file_store_web_hook_url:
        if file_store_web_hook_headers is None:
            # Fallback to default headers. Use the session api key if it is defined in the env.
            file_store_web_hook_headers = {}
            if os.getenv('SESSION_API_KEY'):
                file_store_web_hook_headers['X-Session-API-Key'] = os.getenv(
                    'SESSION_API_KEY'
                )
        store = WebHookFileStore(
            store,
            file_store_web_hook_url,
            httpx.Client(headers=file_store_web_hook_headers or {}),
        )
    return store
