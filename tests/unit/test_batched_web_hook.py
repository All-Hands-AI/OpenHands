import threading
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

    def test_race_condition_timer_vs_size_limit(self, file_store, mock_client):
        """Test race condition where timer and size limit could send same events in multiple batches.

        This test attempts to trigger a race condition where:
        1. A timer is set to send a batch after timeout
        2. Before the timer fires, the size limit is reached
        3. Both the timer and size limit trigger could potentially send the same events
        """
        # Create a store with a longer timeout to increase chance of race condition
        batched_store = BatchedWebHookFileStore(
            file_store=file_store,
            base_url='http://example.com',
            client=mock_client,
            batch_timeout_seconds=0.5,  # Longer timeout
            batch_size_limit_bytes=100,  # Small size limit
        )

        # Track all webhook calls to detect duplicates
        sent_events = []
        original_post = mock_client.post

        def track_post(*args, **kwargs):
            # Extract the batch payload and track events
            if 'json' in kwargs:
                batch_payload = kwargs['json']
                for item in batch_payload:
                    event_key = f'{item["method"]}:{item["path"]}'
                    if 'content' in item:
                        event_key += f':{item["content"]}'
                    sent_events.append(event_key)
            # Return a mock response instead of calling original_post
            response = Mock()
            response.raise_for_status = Mock()
            return response

        mock_client.post.side_effect = track_post

        # Write a small file first to start the timer
        batched_store.write('/small.txt', 'small')

        # Immediately write a large file that will exceed the size limit
        # This should trigger the size limit send while the timer is still running
        large_content = 'x' * 150  # Exceeds the 100 byte limit
        batched_store.write('/large.txt', large_content)

        # Wait for both potential sends to complete
        time.sleep(1.0)

        # Check that each unique event was sent only once
        unique_events = set(sent_events)
        assert len(sent_events) == len(unique_events), (
            f'Duplicate events detected: {sent_events}'
        )

        # Verify the expected events were sent
        expected_events = {'POST:/small.txt:small', 'POST:/large.txt:' + large_content}
        assert unique_events == expected_events

    def test_race_condition_concurrent_flush_and_timer(self, file_store, mock_client):
        """Test race condition between flush() and timer firing simultaneously."""
        batched_store = BatchedWebHookFileStore(
            file_store=file_store,
            base_url='http://example.com',
            client=mock_client,
            batch_timeout_seconds=0.1,  # Short timeout
            batch_size_limit_bytes=1000,
        )

        # Track all webhook calls
        sent_events = []
        call_count = 0
        original_post = mock_client.post

        def track_post(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if 'json' in kwargs:
                batch_payload = kwargs['json']
                for item in batch_payload:
                    event_key = f'{item["method"]}:{item["path"]}'
                    if 'content' in item:
                        event_key += f':{item["content"]}'
                    sent_events.append(event_key)
            # Return a mock response instead of calling original_post
            response = Mock()
            response.raise_for_status = Mock()
            return response

        mock_client.post.side_effect = track_post

        # Write a file to start the timer
        batched_store.write('/test.txt', 'content')

        # Wait almost until the timer would fire, then flush
        time.sleep(0.08)  # Just before the 0.1s timeout
        batched_store.flush()

        # Wait a bit more to see if timer also fires
        time.sleep(0.1)

        # Check that the event was sent only once
        unique_events = set(sent_events)
        assert len(sent_events) == len(unique_events), (
            f'Duplicate events detected: {sent_events}'
        )
        assert 'POST:/test.txt:content' in unique_events

    def test_race_condition_multiple_size_limit_triggers(self, file_store, mock_client):
        """Test race condition where multiple threads could trigger size limit simultaneously."""
        batched_store = BatchedWebHookFileStore(
            file_store=file_store,
            base_url='http://example.com',
            client=mock_client,
            batch_timeout_seconds=10.0,  # Long timeout to avoid timer interference
            batch_size_limit_bytes=50,  # Small size limit
        )

        # Track all webhook calls
        sent_events = []
        original_post = mock_client.post

        def track_post(*args, **kwargs):
            if 'json' in kwargs:
                batch_payload = kwargs['json']
                for item in batch_payload:
                    event_key = f'{item["method"]}:{item["path"]}'
                    if 'content' in item:
                        event_key += f':{item["content"]}'
                    sent_events.append(event_key)
            # Return a mock response instead of calling original_post
            response = Mock()
            response.raise_for_status = Mock()
            return response

        mock_client.post.side_effect = track_post

        # Use multiple threads to write files that will exceed size limit
        def write_large_file(file_num):
            content = 'x' * 60  # Each file exceeds the 50 byte limit
            batched_store.write(f'/file{file_num}.txt', content)

        # Start multiple threads simultaneously
        threads = []
        for i in range(3):
            thread = threading.Thread(target=write_large_file, args=(i,))
            threads.append(thread)

        # Start all threads at roughly the same time
        for thread in threads:
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Wait for any pending webhook calls
        time.sleep(0.5)

        # Check that each unique event was sent only once
        unique_events = set(sent_events)
        assert len(sent_events) == len(unique_events), (
            f'Duplicate events detected: {sent_events}'
        )

        # Verify all expected events were sent
        expected_events = set()
        for i in range(3):
            expected_events.add(f'POST:/file{i}.txt:' + 'x' * 60)

        assert unique_events == expected_events

    def test_race_condition_infinite_recursion_prevention(
        self, file_store, mock_client
    ):
        """Test that race conditions don't cause infinite recursion in _send_batch."""
        batched_store = BatchedWebHookFileStore(
            file_store=file_store,
            base_url='http://example.com',
            client=mock_client,
            batch_timeout_seconds=0.01,  # Very short timeout to trigger race conditions quickly
            batch_size_limit_bytes=10,  # Very small size limit
        )

        # Track webhook calls and detect recursion errors
        call_count = 0
        recursion_errors = []
        original_post = mock_client.post

        def track_post(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            # Return a mock response instead of calling original_post
            response = Mock()
            response.raise_for_status = Mock()
            return response

        mock_client.post.side_effect = track_post

        # Override the _send_batch_request method to catch recursion errors
        original_send_batch_request = batched_store._send_batch_request

        def catch_recursion_errors(*args, **kwargs):
            try:
                return original_send_batch_request(*args, **kwargs)
            except RecursionError as e:
                recursion_errors.append(str(e))
                raise

        batched_store._send_batch_request = catch_recursion_errors

        # Write a file that will trigger both size limit and timer
        batched_store.write('/test.txt', 'content that exceeds limit')

        # Wait for potential recursion to occur
        time.sleep(0.5)

        # Check that no recursion errors occurred
        assert len(recursion_errors) == 0, (
            f'RecursionError detected: {recursion_errors}'
        )

        # The call count should be reasonable (not hundreds of calls)
        assert call_count < 10, (
            f'Too many webhook calls detected: {call_count} (possible infinite loop)'
        )

    def test_race_condition_timer_vs_size_limit_deterministic(
        self, file_store, mock_client
    ):
        """Deterministic test for race condition between timer and size limit using mocks."""
        from unittest.mock import Mock

        # Create a controlled executor that captures tasks without executing them
        mock_executor = Mock()
        submitted_tasks = []

        def mock_submit(fn, *args, **kwargs):
            submitted_tasks.append((fn, args, kwargs))
            return Mock()

        mock_executor.submit = mock_submit

        with patch('openhands.storage.batched_web_hook.EXECUTOR', mock_executor):
            batched_store = BatchedWebHookFileStore(
                file_store=file_store,
                base_url='http://example.com',
                client=mock_client,
                batch_timeout_seconds=0.1,
                batch_size_limit_bytes=50,  # Small size limit
            )

            # Track webhook calls
            sent_events = []

            def track_post(*args, **kwargs):
                if 'json' in kwargs:
                    batch_payload = kwargs['json']
                    for item in batch_payload:
                        event_key = f'{item["method"]}:{item["path"]}'
                        if 'content' in item:
                            event_key += f':{item["content"]}'
                        sent_events.append(event_key)
                # Return a mock response instead of calling original_post
                response = Mock()
                response.raise_for_status = Mock()
                return response

            mock_client.post.side_effect = track_post

            # Write a small file to start the timer
            batched_store.write('/small.txt', 'small')
            assert len(submitted_tasks) == 0  # No size limit exceeded yet
            assert batched_store._batch_timer is not None

            # Write a large file that exceeds size limit
            large_content = 'x' * 60  # Exceeds the 50 byte limit
            batched_store.write('/large.txt', large_content)

            # Size limit should trigger one executor submission
            assert len(submitted_tasks) == 1

            # Manually trigger the timer to simulate race condition
            if batched_store._batch_timer:
                # This simulates the timer firing and submitting another task
                batched_store._batch_timer.function()

            # With the race condition fix, should only have one task (timer prevented)
            assert len(submitted_tasks) == 1, (
                f'Race condition fix failed: expected 1 task, got {len(submitted_tasks)}'
            )

            # Execute the single task
            for fn, args, kwargs in submitted_tasks:
                fn(*args, **kwargs)

            # Check that events are sent correctly without duplicates
            unique_events = set(sent_events)
            assert len(sent_events) == len(unique_events), (
                f'Duplicate events detected: {len(sent_events)} events sent, '
                f'but only {len(unique_events)} unique events'
            )
            
            # Should have exactly 2 unique events (small.txt and large.txt)
            assert len(unique_events) == 2, (
                f'Expected 2 unique events, got {len(unique_events)}: {unique_events}'
            )

    def test_race_condition_concurrent_flush_deterministic(
        self, file_store, mock_client
    ):
        """Deterministic test for race condition between flush and timer using mocks."""
        from unittest.mock import Mock

        mock_executor = Mock()
        submitted_tasks = []

        def mock_submit(fn, *args, **kwargs):
            submitted_tasks.append((fn, args, kwargs))
            return Mock()

        mock_executor.submit = mock_submit

        with patch('openhands.storage.batched_web_hook.EXECUTOR', mock_executor):
            batched_store = BatchedWebHookFileStore(
                file_store=file_store,
                base_url='http://example.com',
                client=mock_client,
                batch_timeout_seconds=0.1,
                batch_size_limit_bytes=1000,  # Large size limit
            )

            # Track webhook calls
            sent_events = []

            def track_post(*args, **kwargs):
                if 'json' in kwargs:
                    batch_payload = kwargs['json']
                    for item in batch_payload:
                        event_key = f'{item["method"]}:{item["path"]}'
                        if 'content' in item:
                            event_key += f':{item["content"]}'
                        sent_events.append(event_key)
                # Return a mock response instead of calling original_post
                response = Mock()
                response.raise_for_status = Mock()
                return response

            mock_client.post.side_effect = track_post

            # Write a file to start the timer
            batched_store.write('/test.txt', 'content')
            assert len(submitted_tasks) == 0  # No size limit exceeded
            assert batched_store._batch_timer is not None

            # Save timer reference before flush cancels it
            original_timer = batched_store._batch_timer
            
            # Call flush() which should send immediately
            batched_store.flush()

            # Flush calls _send_batch directly, so no new executor tasks
            assert len(submitted_tasks) == 0
            
            # Timer should be cancelled after flush
            assert batched_store._batch_timer is None

            # Simulate the original timer firing (race condition)
            if original_timer:
                original_timer.function()

            # With race condition fix, timer should not submit a task (batch is empty)
            assert len(submitted_tasks) == 0, (
                f'Race condition fix failed: timer submitted task after flush'
            )

            # Check that flush sent the event correctly
            unique_events = set(sent_events)
            assert len(sent_events) == len(unique_events), (
                f'Duplicate events detected: {len(sent_events)} events sent, '
                f'but only {len(unique_events)} unique events'
            )
            
            # Should have exactly 1 event from flush
            assert len(unique_events) == 1, (
                f'Expected 1 unique event, got {len(unique_events)}: {unique_events}'
            )

    def test_race_condition_multiple_concurrent_writes_deterministic(
        self, file_store, mock_client
    ):
        """Deterministic test for race condition with multiple concurrent writes."""
        from unittest.mock import Mock

        mock_executor = Mock()
        submitted_tasks = []

        def mock_submit(fn, *args, **kwargs):
            submitted_tasks.append((fn, args, kwargs))
            return Mock()

        mock_executor.submit = mock_submit

        with patch('openhands.storage.batched_web_hook.EXECUTOR', mock_executor):
            batched_store = BatchedWebHookFileStore(
                file_store=file_store,
                base_url='http://example.com',
                client=mock_client,
                batch_timeout_seconds=10.0,  # Long timeout
                batch_size_limit_bytes=30,  # Small size limit
            )

            # Track webhook calls
            sent_events = []

            def track_post(*args, **kwargs):
                if 'json' in kwargs:
                    batch_payload = kwargs['json']
                    for item in batch_payload:
                        event_key = f'{item["method"]}:{item["path"]}'
                        if 'content' in item:
                            event_key += f':{item["content"]}'
                        sent_events.append(event_key)
                # Return a mock response instead of calling original_post
                response = Mock()
                response.raise_for_status = Mock()
                return response

            mock_client.post.side_effect = track_post

            # Write multiple files that each exceed the size limit
            contents = ['x' * 40, 'y' * 40, 'z' * 40]  # Each exceeds 30 byte limit
            for i, content in enumerate(contents):
                batched_store.write(f'/file{i}.txt', content)

            # With race condition fix, only first write should trigger task submission
            # Subsequent writes are prevented by _send_in_progress flag
            assert len(submitted_tasks) == 1, (
                f'Race condition fix failed: expected 1 task, got {len(submitted_tasks)}'
            )

            # Execute the single task
            for fn, args, kwargs in submitted_tasks:
                fn(*args, **kwargs)

            # Check for duplicates
            unique_events = set(sent_events)
            assert len(sent_events) == len(unique_events), (
                f'Duplicate events detected: {len(sent_events)} events sent, '
                f'but only {len(unique_events)} unique events'
            )

            # Should have all 3 files in a single batch (no duplicates)
            expected_events = set()
            for i, content in enumerate(contents):
                expected_events.add(f'POST:/file{i}.txt:{content}')
            assert unique_events == expected_events, (
                f'Expected {expected_events}, got {unique_events}'
            )
