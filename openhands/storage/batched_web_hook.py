import os
import threading
from typing import Optional, Union

import httpx
import tenacity

from openhands.storage.files import FileStore
from openhands.utils.async_utils import EXECUTOR


class BatchedWebHookFileStore(FileStore):
    """
    File store which batches updates before sending them to a webhook.

    This class wraps another FileStore implementation and sends HTTP requests
    to a specified URL when files are written or deleted. Updates are batched
    and sent together after a certain amount of time passes or if the content
    size exceeds a threshold.

    Attributes:
        file_store: The underlying FileStore implementation
        base_url: The base URL for webhook requests
        client: The HTTP client used to make webhook requests
        batch_timeout_seconds: Time in seconds after which a batch is sent (default: 5)
        batch_size_limit_bytes: Size limit in bytes after which a batch is sent (default: 1048576 (1MB))
        _batch_lock: Lock for thread-safe access to the batch
        _batch: Dictionary of pending file updates
        _batch_timer: Timer for sending batches after timeout
        _batch_size: Current size of the batch in bytes
    """

    file_store: FileStore
    base_url: str
    client: httpx.Client
    batch_timeout_seconds: float
    batch_size_limit_bytes: int
    _batch_lock: threading.Lock
    _batch: dict[str, tuple[str, Optional[Union[str, bytes]]]]
    _batch_timer: Optional[threading.Timer]
    _batch_size: int

    def __init__(
        self,
        file_store: FileStore,
        base_url: str,
        client: Optional[httpx.Client] = None,
        batch_timeout_seconds: Optional[float] = None,
        batch_size_limit_bytes: Optional[int] = None,
    ):
        """
        Initialize a BatchedWebHookFileStore.

        Args:
            file_store: The underlying FileStore implementation
            base_url: The base URL for webhook requests
            client: Optional HTTP client to use for requests. If None, a new client will be created.
            batch_timeout_seconds: Time in seconds after which a batch is sent.
                If None, uses WEBHOOK_BATCH_TIMEOUT_SECONDS env var or defaults to 5.
            batch_size_limit_bytes: Size limit in bytes after which a batch is sent.
                If None, uses WEBHOOK_BATCH_SIZE_LIMIT_BYTES env var or defaults to 1MB.
        """
        self.file_store = file_store
        self.base_url = base_url
        if client is None:
            client = httpx.Client()
        self.client = client

        # Get batch timeout from environment variable or use default
        self.batch_timeout_seconds = batch_timeout_seconds or float(
            os.environ.get('WEBHOOK_BATCH_TIMEOUT_SECONDS', '5.0')
        )

        # Get batch size limit from environment variable or use default (1MB)
        self.batch_size_limit_bytes = batch_size_limit_bytes or int(
            os.environ.get('WEBHOOK_BATCH_SIZE_LIMIT_BYTES', '1048576')
        )

        # Initialize batch state
        self._batch_lock = threading.Lock()
        self._batch = {}  # Maps path -> (operation, content)
        self._batch_timer = None
        self._batch_size = 0

    def write(self, path: str, contents: Union[str, bytes]) -> None:
        """
        Write contents to a file and queue a webhook update.

        Args:
            path: The path to write to
            contents: The contents to write
        """
        self.file_store.write(path, contents)
        self._queue_update(path, 'write', contents)

    def read(self, path: str) -> str:
        """
        Read contents from a file.

        Args:
            path: The path to read from

        Returns:
            The contents of the file
        """
        return self.file_store.read(path)

    def list(self, path: str) -> list[str]:
        """
        List files in a directory.

        Args:
            path: The directory path to list

        Returns:
            A list of file paths
        """
        return self.file_store.list(path)

    def delete(self, path: str) -> None:
        """
        Delete a file and queue a webhook update.

        Args:
            path: The path to delete
        """
        self.file_store.delete(path)
        self._queue_update(path, 'delete', None)

    def _queue_update(
        self, path: str, operation: str, contents: Optional[Union[str, bytes]]
    ) -> None:
        """
        Queue an update to be sent to the webhook.

        Args:
            path: The path that was modified
            operation: The operation performed ("write" or "delete")
            contents: The contents that were written (None for delete operations)
        """
        with self._batch_lock:
            # Calculate content size
            content_size = 0
            if contents is not None:
                if isinstance(contents, str):
                    content_size = len(contents.encode('utf-8'))
                else:
                    content_size = len(contents)

            # Update batch size calculation
            # If this path already exists in the batch, subtract its previous size
            if path in self._batch:
                prev_op, prev_contents = self._batch[path]
                if prev_contents is not None:
                    if isinstance(prev_contents, str):
                        self._batch_size -= len(prev_contents.encode('utf-8'))
                    else:
                        self._batch_size -= len(prev_contents)

            # Add new content size
            self._batch_size += content_size

            # Add to batch
            self._batch[path] = (operation, contents)

            # Check if we need to send the batch due to size limit
            if self._batch_size >= self.batch_size_limit_bytes:
                # Submit to executor to avoid blocking
                EXECUTOR.submit(self._send_batch)
                return

            # Start or reset the timer for sending the batch
            if self._batch_timer is not None:
                self._batch_timer.cancel()
                self._batch_timer = None

            timer = threading.Timer(
                self.batch_timeout_seconds, self._send_batch_from_timer
            )
            timer.daemon = True
            timer.start()
            self._batch_timer = timer

    def _send_batch_from_timer(self) -> None:
        """
        Send the batch from the timer thread.
        This method is called by the timer and submits the actual sending to the executor.
        """
        EXECUTOR.submit(self._send_batch)

    def _send_batch(self) -> None:
        """
        Send the current batch of updates to the webhook.
        This method acquires the batch lock and processes all pending updates.
        """
        batch_to_send: dict[str, tuple[str, Optional[Union[str, bytes]]]] = {}

        with self._batch_lock:
            if not self._batch:
                return

            # Copy the batch and clear the current one
            batch_to_send = self._batch.copy()
            self._batch.clear()
            self._batch_size = 0

            # Cancel any pending timer
            if self._batch_timer is not None:
                self._batch_timer.cancel()
                self._batch_timer = None

        # Process the batch outside the lock
        for path, (operation, contents) in batch_to_send.items():
            try:
                if operation == 'write':
                    self._send_write(path, contents)
                elif operation == 'delete':
                    self._send_delete(path)
            except Exception as e:
                # Log the error but continue processing other items
                print(f'Error sending webhook for {path}: {e}')

    @tenacity.retry(
        wait=tenacity.wait_fixed(1),
        stop=tenacity.stop_after_attempt(3),
    )
    def _send_write(self, path: str, contents: Union[str, bytes]) -> None:
        """
        Send a POST request to the webhook URL for a file write operation.

        This method is retried up to 3 times with a 1-second delay between attempts.

        Args:
            path: The path that was written to
            contents: The contents that were written

        Raises:
            httpx.HTTPStatusError: If the webhook request fails
        """
        base_url = self.base_url + path
        response = self.client.post(base_url, content=contents)
        response.raise_for_status()

    @tenacity.retry(
        wait=tenacity.wait_fixed(1),
        stop=tenacity.stop_after_attempt(3),
    )
    def _send_delete(self, path: str) -> None:
        """
        Send a DELETE request to the webhook URL for a file delete operation.

        This method is retried up to 3 times with a 1-second delay between attempts.

        Args:
            path: The path that was deleted

        Raises:
            httpx.HTTPStatusError: If the webhook request fails
        """
        base_url = self.base_url + path
        response = self.client.delete(base_url)
        response.raise_for_status()

    def flush(self) -> None:
        """
        Immediately send any pending updates to the webhook.
        This can be called to ensure all updates are sent before shutting down.
        """
        self._send_batch()
