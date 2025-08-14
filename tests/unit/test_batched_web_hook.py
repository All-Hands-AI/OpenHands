import threading
import time
from unittest.mock import MagicMock

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
        # Create a proper mock response that doesn't cause recursion
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        client.post.return_value = mock_response
        client.delete.return_value = mock_response
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

        # Now the client should have been called with a batch payload
        mock_client.post.assert_called_once()
        args, kwargs = mock_client.post.call_args
        assert args[0] == 'http://example.com'
        assert 'json' in kwargs

        # Check the batch payload
        batch_payload = kwargs['json']
        assert isinstance(batch_payload, list)
        assert len(batch_payload) == 1
        assert batch_payload[0]['method'] == 'POST'
        assert batch_payload[0]['path'] == '/test.txt'
        assert batch_payload[0]['content'] == 'Hello, world!'

    def test_delete_operation_batched(self, batched_store, mock_client):
        # Write and then delete a file
        batched_store.write('/test.txt', 'Hello, world!')
        batched_store.delete('/test.txt')

        # The client should not have been called yet
        mock_client.post.assert_not_called()

        # Wait for the batch timeout
        time.sleep(0.2)

        # Now the client should have been called with a batch payload
        mock_client.post.assert_called_once()
        args, kwargs = mock_client.post.call_args
        assert args[0] == 'http://example.com'
        assert 'json' in kwargs

        # Check the batch payload
        batch_payload = kwargs['json']
        assert isinstance(batch_payload, list)
        assert len(batch_payload) == 1
        assert batch_payload[0]['method'] == 'DELETE'
        assert batch_payload[0]['path'] == '/test.txt'
        assert 'content' not in batch_payload[0]

    def test_batch_size_limit_triggers_send(self, batched_store, mock_client):
        # Write a large file that exceeds the batch size limit
        large_content = 'x' * 1001  # Exceeds the 1000 byte limit
        batched_store.write('/large.txt', large_content)

        # The batch might be sent asynchronously, so we need to wait a bit
        time.sleep(0.2)

        # The client should have been called due to size limit
        mock_client.post.assert_called_once()
        args, kwargs = mock_client.post.call_args
        assert args[0] == 'http://example.com'
        assert 'json' in kwargs

        # Check the batch payload
        batch_payload = kwargs['json']
        assert isinstance(batch_payload, list)
        assert len(batch_payload) == 1
        assert batch_payload[0]['method'] == 'POST'
        assert batch_payload[0]['path'] == '/large.txt'
        assert batch_payload[0]['content'] == large_content

    def test_multiple_updates_same_file(self, batched_store, mock_client):
        # Write to the same file multiple times
        batched_store.write('/test.txt', 'Version 1')
        batched_store.write('/test.txt', 'Version 2')
        batched_store.write('/test.txt', 'Version 3')

        # Wait for the batch timeout
        time.sleep(0.2)

        # Only the latest version should be sent
        mock_client.post.assert_called_once()
        args, kwargs = mock_client.post.call_args
        assert args[0] == 'http://example.com'
        assert 'json' in kwargs

        # Check the batch payload
        batch_payload = kwargs['json']
        assert isinstance(batch_payload, list)
        assert len(batch_payload) == 1
        assert batch_payload[0]['method'] == 'POST'
        assert batch_payload[0]['path'] == '/test.txt'
        assert batch_payload[0]['content'] == 'Version 3'

    def test_flush_sends_immediately(self, batched_store, mock_client):
        # Write a file
        batched_store.write('/test.txt', 'Hello, world!')

        # The client should not have been called yet
        mock_client.post.assert_not_called()

        # Flush the batch
        batched_store.flush()

        # Now the client should have been called without waiting for timeout
        mock_client.post.assert_called_once()
        args, kwargs = mock_client.post.call_args
        assert args[0] == 'http://example.com'
        assert 'json' in kwargs

        # Check the batch payload
        batch_payload = kwargs['json']
        assert isinstance(batch_payload, list)
        assert len(batch_payload) == 1
        assert batch_payload[0]['method'] == 'POST'
        assert batch_payload[0]['path'] == '/test.txt'
        assert batch_payload[0]['content'] == 'Hello, world!'

    def test_multiple_operations_in_single_batch(self, batched_store, mock_client):
        # Perform multiple operations
        batched_store.write('/file1.txt', 'Content 1')
        batched_store.write('/file2.txt', 'Content 2')
        batched_store.delete('/file3.txt')

        # Wait for the batch timeout
        time.sleep(0.2)

        # Check that only one POST request was made with all operations
        mock_client.post.assert_called_once()
        args, kwargs = mock_client.post.call_args
        assert args[0] == 'http://example.com'
        assert 'json' in kwargs

        # Check the batch payload
        batch_payload = kwargs['json']
        assert isinstance(batch_payload, list)
        assert len(batch_payload) == 3

        # Check each operation in the batch
        operations = {item['path']: item for item in batch_payload}

        assert '/file1.txt' in operations
        assert operations['/file1.txt']['method'] == 'POST'
        assert operations['/file1.txt']['content'] == 'Content 1'

        assert '/file2.txt' in operations
        assert operations['/file2.txt']['method'] == 'POST'
        assert operations['/file2.txt']['content'] == 'Content 2'

        assert '/file3.txt' in operations
        assert operations['/file3.txt']['method'] == 'DELETE'
        assert 'content' not in operations['/file3.txt']

    def test_binary_content_handling(self, batched_store, mock_client):
        # Write binary content
        binary_content = b'\x00\x01\x02\x03\xff\xfe\xfd\xfc'
        batched_store.write('/binary.bin', binary_content)

        # Wait for the batch timeout
        time.sleep(0.2)

        # Check that the client was called
        mock_client.post.assert_called_once()
        args, kwargs = mock_client.post.call_args
        assert args[0] == 'http://example.com'
        assert 'json' in kwargs

        # Check the batch payload
        batch_payload = kwargs['json']
        assert isinstance(batch_payload, list)
        assert len(batch_payload) == 1

        # Binary content should be base64 encoded
        assert batch_payload[0]['method'] == 'POST'
        assert batch_payload[0]['path'] == '/binary.bin'
        assert 'content' in batch_payload[0]
        assert 'encoding' in batch_payload[0]
        assert batch_payload[0]['encoding'] == 'base64'

        # Verify the content can be decoded back to the original binary
        import base64

        decoded = base64.b64decode(batch_payload[0]['content'].encode('ascii'))
        assert decoded == binary_content

    def test_race_condition_multiple_size_triggers(self, file_store, mock_client):
        """Test race condition where multiple threads trigger size limit simultaneously."""
        # Create a store with a very small size limit to easily trigger the condition
        batched_store = BatchedWebHookFileStore(
            file_store=file_store,
            base_url='http://example.com',
            client=mock_client,
            batch_timeout_seconds=10.0,  # Long timeout so only size triggers
            batch_size_limit_bytes=100,  # Small limit to easily trigger
        )

        # Track all calls to post method
        call_count = 0

        def counting_post(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            # Return the mock response directly instead of calling original_post
            mock_response = MagicMock()
            mock_response.raise_for_status = MagicMock()
            return mock_response

        mock_client.post.side_effect = counting_post

        # Create multiple threads that will simultaneously add content to trigger size limit
        num_threads = 5
        content_size = (
            50  # Each content is 50 bytes, so 2 should trigger the 100 byte limit
        )
        threads = []
        results = []

        def write_large_content(thread_id):
            try:
                content = f'Thread {thread_id} content: ' + 'x' * content_size
                batched_store.write(f'/file_{thread_id}.txt', content)
                results.append(f'Thread {thread_id} completed')
            except Exception as e:
                results.append(f'Thread {thread_id} error: {e}')

        # Start all threads simultaneously
        for i in range(num_threads):
            thread = threading.Thread(target=write_large_content, args=(i,))
            threads.append(thread)

        # Start all threads at roughly the same time
        for thread in threads:
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join(timeout=5.0)

        # Wait a bit for any async operations to complete
        time.sleep(0.5)

        # Verify all threads completed successfully
        assert len(results) == num_threads
        for result in results:
            assert 'completed' in result, f'Unexpected result: {result}'

        # Verify that webhook calls were made (should be multiple due to size triggers)
        assert call_count > 0, 'No webhook calls were made'

        # Collect all the data that was sent
        all_sent_data = {}
        for call_args in mock_client.post.call_args_list:
            args, kwargs = call_args
            batch_payload = kwargs['json']
            for item in batch_payload:
                path = item['path']
                all_sent_data[path] = item

        # Verify that all files were sent exactly once (no duplicates or missing files)
        expected_files = {f'/file_{i}.txt' for i in range(num_threads)}
        sent_files = set(all_sent_data.keys())
        assert sent_files == expected_files, (
            f'Expected {expected_files}, got {sent_files}'
        )

        # Verify content integrity
        for i in range(num_threads):
            path = f'/file_{i}.txt'
            expected_content = f'Thread {i} content: ' + 'x' * content_size
            assert all_sent_data[path]['content'] == expected_content
            assert all_sent_data[path]['method'] == 'POST'

    def test_race_condition_timer_vs_size_trigger(self, file_store, mock_client):
        """Test race condition between timer expiration and size limit trigger."""
        batched_store = BatchedWebHookFileStore(
            file_store=file_store,
            base_url='http://example.com',
            client=mock_client,
            batch_timeout_seconds=0.2,  # Short timeout
            batch_size_limit_bytes=200,  # Medium size limit
        )

        # Track calls to ensure no duplicates
        call_data = []

        def tracking_post(*args, **kwargs):
            call_data.append(kwargs['json'])
            # Return the mock response directly instead of calling original_post
            mock_response = MagicMock()
            mock_response.raise_for_status = MagicMock()
            return mock_response

        mock_client.post.side_effect = tracking_post

        # Add some content that's close to but under the size limit
        batched_store.write('/file1.txt', 'x' * 80)  # 80 bytes
        batched_store.write('/file2.txt', 'y' * 80)  # 80 bytes, total 160 bytes

        # Wait a bit, then add content that will trigger size limit
        # This creates a race between the timer (which should fire soon) and size trigger
        time.sleep(0.1)  # Wait half the timeout period

        # This should trigger the size limit (160 + 60 = 220 > 200)
        batched_store.write('/file3.txt', 'z' * 60)

        # Wait for both timer and size-triggered sends to potentially complete
        time.sleep(0.5)

        # Verify that we got the expected data without duplication
        assert len(call_data) >= 1, 'At least one webhook call should have been made'

        # Collect all sent files across all calls
        all_sent_files = {}
        for batch_payload in call_data:
            for item in batch_payload:
                path = item['path']
                # If we see the same file twice, that's a problem
                assert path not in all_sent_files, (
                    f'File {path} was sent multiple times'
                )
                all_sent_files[path] = item

        # Verify all files were sent exactly once
        expected_files = {'/file1.txt', '/file2.txt', '/file3.txt'}
        sent_files = set(all_sent_files.keys())
        assert sent_files == expected_files, (
            f'Expected {expected_files}, got {sent_files}'
        )

        # Verify content integrity
        assert all_sent_files['/file1.txt']['content'] == 'x' * 80
        assert all_sent_files['/file2.txt']['content'] == 'y' * 80
        assert all_sent_files['/file3.txt']['content'] == 'z' * 60

    def test_race_condition_concurrent_batch_sends(self, file_store, mock_client):
        """Test race condition where _send_batch is called concurrently from multiple sources."""
        batched_store = BatchedWebHookFileStore(
            file_store=file_store,
            base_url='http://example.com',
            client=mock_client,
            batch_timeout_seconds=0.1,  # Very short timeout
            batch_size_limit_bytes=50,  # Very small size limit
        )

        # Use a lock to simulate slow webhook processing and increase chance of race
        webhook_lock = threading.Lock()
        call_order = []

        def slow_post(*args, **kwargs):
            with webhook_lock:
                call_order.append(len(kwargs['json']))  # Record batch size
                time.sleep(0.05)  # Simulate slow webhook processing
                # Return the mock response directly instead of calling original_post
                mock_response = MagicMock()
                mock_response.raise_for_status = MagicMock()
                return mock_response

        mock_client.post.side_effect = slow_post

        # Create a scenario where both timer and size limit can trigger simultaneously
        def writer_thread(thread_id):
            for i in range(3):
                content = f'Thread{thread_id}_File{i}: ' + 'x' * 20  # ~40 bytes each
                batched_store.write(f'/t{thread_id}_f{i}.txt', content)
                time.sleep(0.02)  # Small delay between writes

        # Start multiple writer threads
        threads = []
        for i in range(3):
            thread = threading.Thread(target=writer_thread, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join(timeout=2.0)

        # Wait for any remaining async operations
        time.sleep(0.5)

        # Verify that webhook was called
        assert len(call_order) > 0, 'No webhook calls were made'

        # Collect all sent data to verify no duplicates or missing files
        all_sent_files = {}
        for call_args in mock_client.post.call_args_list:
            args, kwargs = call_args
            batch_payload = kwargs['json']
            for item in batch_payload:
                path = item['path']
                assert path not in all_sent_files, (
                    f'File {path} was sent multiple times'
                )
                all_sent_files[path] = item

        # Verify all expected files were sent
        expected_files = set()
        for thread_id in range(3):
            for file_id in range(3):
                expected_files.add(f'/t{thread_id}_f{file_id}.txt')

        sent_files = set(all_sent_files.keys())
        assert sent_files == expected_files, (
            f'Expected {expected_files}, got {sent_files}'
        )

    def test_race_condition_with_real_synchronization(self, file_store, mock_client):
        """Test that our synchronization fixes prevent race conditions."""
        batched_store = BatchedWebHookFileStore(
            file_store=file_store,
            base_url='http://example.com',
            client=mock_client,
            batch_timeout_seconds=0.1,  # Short timeout
            batch_size_limit_bytes=100,  # Small size limit
        )

        # Track calls to ensure no duplicates
        call_data = []
        call_lock = threading.Lock()

        def tracking_post(*args, **kwargs):
            with call_lock:
                call_data.append(kwargs['json'])
            # Return the mock response directly
            mock_response = MagicMock()
            mock_response.raise_for_status = MagicMock()
            return mock_response

        mock_client.post.side_effect = tracking_post

        # Create a scenario that would trigger race conditions without synchronization
        def writer_thread(thread_id):
            for i in range(5):
                content = f'Thread{thread_id}_File{i}: ' + 'x' * 20  # ~40 bytes each
                batched_store.write(f'/t{thread_id}_f{i}.txt', content)
                time.sleep(0.01)  # Small delay between writes

        # Start multiple writer threads to create concurrent load
        threads = []
        for i in range(3):
            thread = threading.Thread(target=writer_thread, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join(timeout=2.0)

        # Wait for any pending batches to be sent
        time.sleep(0.5)

        # Verify that no files were sent multiple times
        all_sent_files = set()
        for batch_payload in call_data:
            for item in batch_payload:
                path = item['path']
                assert path not in all_sent_files, (
                    f'File {path} was sent multiple times across batches'
                )
                all_sent_files.add(path)

        # Verify all expected files were sent
        expected_files = set()
        for thread_id in range(3):
            for file_id in range(5):
                expected_files.add(f'/t{thread_id}_f{file_id}.txt')
        
        assert all_sent_files == expected_files, (
            f'Expected {len(expected_files)} files, but got {len(all_sent_files)}'
        )
