import threading
from typing import Optional, Union

import httpx
import tenacity

from openhands.storage.files import FileStore
from openhands.utils.async_utils import EXECUTOR

# Constants for batching configuration
WEBHOOK_BATCH_TIMEOUT_SECONDS = 5.0
WEBHOOK_BATCH_SIZE_LIMIT_BYTES = 1048576  # 1MB


class BatchedWebHookFileStore(FileStore):
    """File store which batches updates before sending them to a webhook.

    This class wraps another FileStore implementation and sends HTTP requests
    to a specified URL when files are written or deleted. Updates are batched
    and sent together after a certain amount of time passes or if the content
    size exceeds a threshold.

    Attributes:
        file_store: The underlying FileStore implementation
        base_url: The base URL for webhook requests
        client: The HTTP client used to make webhook requests
        batch_timeout_seconds: Time in seconds after which a batch is sent (default: WEBHOOK_BATCH_TIMEOUT_SECONDS)
        batch_size_limit_bytes: Size limit in bytes after which a batch is sent (default: WEBHOOK_BATCH_SIZE_LIMIT_BYTES)
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
    _timer_generation: int

    def __init__(
        self,
        file_store: FileStore,
        base_url: str,
        client: Optional[httpx.Client] = None,
        batch_timeout_seconds: Optional[float] = None,
        batch_size_limit_bytes: Optional[int] = None,
    ):
        """Initialize a BatchedWebHookFileStore.

        Args:
            file_store: The underlying FileStore implementation
            base_url: The base URL for webhook requests
            client: Optional HTTP client to use for requests. If None, a new client will be created.
            batch_timeout_seconds: Time in seconds after which a batch is sent.
                If None, uses the default constant WEBHOOK_BATCH_TIMEOUT_SECONDS.
            batch_size_limit_bytes: Size limit in bytes after which a batch is sent.
                If None, uses the default constant WEBHOOK_BATCH_SIZE_LIMIT_BYTES.
        """
        self.file_store = file_store
        self.base_url = base_url
        if client is None:
            client = httpx.Client()
        self.client = client

        # Use provided values or default constants
        self.batch_timeout_seconds = (
            batch_timeout_seconds or WEBHOOK_BATCH_TIMEOUT_SECONDS
        )
        self.batch_size_limit_bytes = (
            batch_size_limit_bytes or WEBHOOK_BATCH_SIZE_LIMIT_BYTES
        )

        # Initialize batch state
        self._batch_lock = threading.Lock()
        self._batch = {}  # Maps path -> (operation, content)
        self._batch_timer = None
        self._batch_size = 0
        self._timer_generation = 0

    def write(self, path: str, contents: Union[str, bytes]) -> None:
        """Write contents to a file and queue a webhook update.

        Args:
            path: The path to write to
            contents: The contents to write
        """
        self.file_store.write(path, contents)
        self._queue_update(path, 'write', contents)

    def read(self, path: str) -> str:
        """Read contents from a file.

        Args:
            path: The path to read from

        Returns:
            The contents of the file
        """
        return self.file_store.read(path)

    def list(self, path: str) -> list[str]:
        """List files in a directory.

        Args:
            path: The directory path to list

        Returns:
            A list of file paths
        """
        return self.file_store.list(path)

    def delete(self, path: str) -> None:
        """Delete a file and queue a webhook update.

        Args:
            path: The path to delete
        """
        self.file_store.delete(path)
        self._queue_update(path, 'delete', None)

    def _queue_update(
        self, path: str, operation: str, contents: Optional[Union[str, bytes]]
    ) -> None:
        """Queue an update to be sent to the webhook.

        Args:
            path: The path that was modified
            operation: The operation performed ("write" or "delete")
            contents: The contents that were written (None for delete operations)
        """
        batch_to_send = None
        
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
                # Move current batch to pending and clear current batch
                batch_to_send = self._batch.copy()
                self._batch.clear()
                self._batch_size = 0
                
                # Cancel any pending timer since we're sending now
                if self._batch_timer is not None:
                    self._batch_timer.cancel()
                    self._batch_timer = None
                self._timer_generation += 1
            else:
                # Start or reset the timer for sending the batch
                if self._batch_timer is not None:
                    self._batch_timer.cancel()
                    self._batch_timer = None

                self._timer_generation += 1
                current_generation = self._timer_generation
                timer = threading.Timer(
                    self.batch_timeout_seconds, 
                    lambda: self._send_batch_from_timer(current_generation)
                )
                timer.daemon = True
                timer.start()
                self._batch_timer = timer
        
        # Send the batch outside the lock if needed
        if batch_to_send:
            EXECUTOR.submit(self._send_batch_request_with_error_handling, batch_to_send)

    def _send_batch_from_timer(self, generation: int) -> None:
        """Send the batch from the timer thread.
        This method is called by the timer and submits the actual sending to the executor.
        
        Args:
            generation: The timer generation to ensure only current timer executes
        """
        batch_to_send = None
        
        with self._batch_lock:
            # Only proceed if this is the current timer generation and there's something to send
            if generation == self._timer_generation and self._batch:
                # Move current batch to pending and clear current batch
                batch_to_send = self._batch.copy()
                self._batch.clear()
                self._batch_size = 0
                self._batch_timer = None
        
        # Send the batch outside the lock if needed
        if batch_to_send:
            EXECUTOR.submit(self._send_batch_request_with_error_handling, batch_to_send)

    def _send_batch_request_with_error_handling(
        self, batch: dict[str, tuple[str, Optional[Union[str, bytes]]]]
    ) -> None:
        """Wrapper for _send_batch_request that handles errors."""
        try:
            self._send_batch_request(batch)
        except Exception as e:
            # Log the error
            print(f'Error sending webhook batch: {e}')

    @tenacity.retry(
        wait=tenacity.wait_fixed(1),
        stop=tenacity.stop_after_attempt(3),
    )
    def _send_batch_request(
        self, batch: dict[str, tuple[str, Optional[Union[str, bytes]]]]
    ) -> None:
        """Send a single batch request to the webhook URL with all updates.

        This method is retried up to 3 times with a 1-second delay between attempts.

        Args:
            batch: Dictionary mapping paths to (operation, contents) tuples

        Raises:
            httpx.HTTPStatusError: If the webhook request fails
        """
        # Prepare the batch payload
        batch_payload = []

        for path, (operation, contents) in batch.items():
            item = {
                'method': 'POST' if operation == 'write' else 'DELETE',
                'path': path,
            }

            if operation == 'write' and contents is not None:
                # Convert bytes to string if needed
                if isinstance(contents, bytes):
                    try:
                        # Try to decode as UTF-8
                        item['content'] = contents.decode('utf-8')
                    except UnicodeDecodeError:
                        # If not UTF-8, use base64 encoding
                        import base64

                        item['content'] = base64.b64encode(contents).decode('ascii')
                        item['encoding'] = 'base64'
                else:
                    item['content'] = contents

            batch_payload.append(item)

        # Send the batch as a single request
        response = self.client.post(self.base_url, json=batch_payload)
        response.raise_for_status()

    def flush(self) -> None:
        """Immediately send any pending updates to the webhook.
        This can be called to ensure all updates are sent before shutting down.
        """
        batch_to_send = None
        
        with self._batch_lock:
            # Only proceed if there's something to send
            if self._batch:
                # Move current batch to pending and clear current batch
                batch_to_send = self._batch.copy()
                self._batch.clear()
                self._batch_size = 0
                
                # Cancel any pending timer since we're sending now
                if self._batch_timer is not None:
                    self._batch_timer.cancel()
                    self._batch_timer = None
                self._timer_generation += 1
        
        # Send the batch directly (not through executor) for immediate sending
        if batch_to_send:
            self._send_batch_request_with_error_handling(batch_to_send)
