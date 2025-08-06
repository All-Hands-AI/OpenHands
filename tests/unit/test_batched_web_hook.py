import os
import time
from unittest.mock import MagicMock, patch

import httpx
import pytest

from openhands.storage.batched_web_hook import BatchedWebHookFileStore
from openhands.storage.files import FileStore


class MockFileStore(FileStore):
    def __init__(self):
        self.files = {}

    def write(self, path: str, contents: str | bytes) -> None:
        self.files[path] = contents

    def read(self, path: str) -> str:
        return self.files.get(path, '')

    def list(self, path: str) -> list[str]:
        return [k for k in self.files.keys() if k.startswith(path)]

    def delete(self, path: str) -> None:
        if path in self.files:
            del self.files[path]


class TestBatchedWebHookFileStore:
    @pytest.fixture
    def mock_client(self):
        client = MagicMock(spec=httpx.Client)
        client.post.return_value.raise_for_status = MagicMock()
        client.delete.return_value.raise_for_status = MagicMock()
        return client

    @pytest.fixture
    def file_store(self):
        return MockFileStore()

    @pytest.fixture
    def batched_store(self, file_store, mock_client):
        # Use a short timeout for testing
        return BatchedWebHookFileStore(
            file_store=file_store,
            base_url='http://example.com',
            client=mock_client,
            batch_timeout_seconds=0.1,  # Short timeout for testing
            batch_size_limit_bytes=1000,
        )

    def test_write_operation_batched(self, batched_store, mock_client):
        # Write a file
        batched_store.write('/test.txt', 'Hello, world!')

        # The client should not have been called yet
        mock_client.post.assert_not_called()

        # Wait for the batch timeout
        time.sleep(0.2)

        # Now the client should have been called
        mock_client.post.assert_called_once_with(
            'http://example.com/test.txt', content='Hello, world!'
        )

    def test_delete_operation_batched(self, batched_store, mock_client):
        # Write and then delete a file
        batched_store.write('/test.txt', 'Hello, world!')
        batched_store.delete('/test.txt')

        # The client should not have been called yet
        mock_client.delete.assert_not_called()

        # Wait for the batch timeout
        time.sleep(0.2)

        # Now the client should have been called
        mock_client.delete.assert_called_once_with('http://example.com/test.txt')

    def test_batch_size_limit_triggers_send(self, batched_store, mock_client):
        # Write a large file that exceeds the batch size limit
        large_content = 'x' * 1001  # Exceeds the 1000 byte limit
        batched_store.write('/large.txt', large_content)

        # The client should have been called immediately due to size
        mock_client.post.assert_called_once_with(
            'http://example.com/large.txt', content=large_content
        )

    def test_multiple_updates_same_file(self, batched_store, mock_client):
        # Write to the same file multiple times
        batched_store.write('/test.txt', 'Version 1')
        batched_store.write('/test.txt', 'Version 2')
        batched_store.write('/test.txt', 'Version 3')

        # Wait for the batch timeout
        time.sleep(0.2)

        # Only the latest version should be sent
        mock_client.post.assert_called_once_with(
            'http://example.com/test.txt', content='Version 3'
        )

    def test_flush_sends_immediately(self, batched_store, mock_client):
        # Write a file
        batched_store.write('/test.txt', 'Hello, world!')

        # The client should not have been called yet
        mock_client.post.assert_not_called()

        # Flush the batch
        batched_store.flush()

        # Now the client should have been called without waiting for timeout
        mock_client.post.assert_called_once_with(
            'http://example.com/test.txt', content='Hello, world!'
        )

    def test_environment_variables(self):
        # Test that environment variables are used for configuration
        with patch.dict(
            os.environ,
            {
                'WEBHOOK_BATCH_TIMEOUT_SECONDS': '10.0',
                'WEBHOOK_BATCH_SIZE_LIMIT_BYTES': '2000',
            },
        ):
            file_store = MockFileStore()
            client = MagicMock(spec=httpx.Client)

            batched_store = BatchedWebHookFileStore(
                file_store=file_store,
                base_url='http://example.com',
                client=client,
            )

            assert batched_store.batch_timeout_seconds == 10.0
            assert batched_store.batch_size_limit_bytes == 2000
