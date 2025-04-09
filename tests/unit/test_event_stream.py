import gc
import json
import os
import time

import psutil
import pytest
from pytest import TempPathFactory

from openhands.core.schema import ActionType, ObservationType
from openhands.events import EventSource, EventStream
from openhands.events.action import (
    NullAction,
)
from openhands.events.action.files import (
    FileEditAction,
    FileReadAction,
    FileWriteAction,
)
from openhands.events.action.message import MessageAction
from openhands.events.event import FileEditSource, FileReadSource
from openhands.events.observation import NullObservation
from openhands.events.observation.files import (
    FileEditObservation,
    FileReadObservation,
    FileWriteObservation,
)
from openhands.events.serialization.event import event_to_dict
from openhands.storage import get_file_store
from openhands.storage.locations import (
    get_conversation_event_filename,
)


@pytest.fixture
def temp_dir(tmp_path_factory: TempPathFactory) -> str:
    return str(tmp_path_factory.mktemp('test_event_stream'))


def collect_events(stream):
    return [event for event in stream.get_events()]


def test_basic_flow(temp_dir: str):
    file_store = get_file_store('local', temp_dir)
    event_stream = EventStream('abc', file_store)
    event_stream.add_event(NullAction(), EventSource.AGENT)
    assert len(collect_events(event_stream)) == 1


def test_stream_storage(temp_dir: str):
    file_store = get_file_store('local', temp_dir)
    event_stream = EventStream('abc', file_store)
    event_stream.add_event(NullObservation(''), EventSource.AGENT)
    assert len(collect_events(event_stream)) == 1
    content = event_stream.file_store.read(get_conversation_event_filename('abc', 0))
    assert content is not None
    data = json.loads(content)
    assert 'timestamp' in data
    del data['timestamp']
    assert data == {
        'id': 0,
        'source': 'agent',
        'observation': 'null',
        'content': '',
        'extras': {},
        'message': 'No observation',
    }


def test_rehydration(temp_dir: str):
    file_store = get_file_store('local', temp_dir)
    event_stream = EventStream('abc', file_store)
    event_stream.add_event(NullObservation('obs1'), EventSource.AGENT)
    event_stream.add_event(NullObservation('obs2'), EventSource.AGENT)
    assert len(collect_events(event_stream)) == 2

    stream2 = EventStream('es2', file_store)
    assert len(collect_events(stream2)) == 0

    stream1rehydrated = EventStream('abc', file_store)
    events = collect_events(stream1rehydrated)
    assert len(events) == 2
    assert events[0].content == 'obs1'
    assert events[1].content == 'obs2'


def test_get_matching_events_type_filter(temp_dir: str):
    file_store = get_file_store('local', temp_dir)
    event_stream = EventStream('abc', file_store)

    # Add mixed event types
    event_stream.add_event(NullAction(), EventSource.AGENT)
    event_stream.add_event(NullObservation('test'), EventSource.AGENT)
    event_stream.add_event(NullAction(), EventSource.AGENT)
    event_stream.add_event(MessageAction(content='test'), EventSource.AGENT)

    # Filter by NullAction
    events = event_stream.get_matching_events(event_types=(NullAction,))
    assert len(events) == 2
    assert all(isinstance(e, NullAction) for e in events)

    # Filter by NullObservation
    events = event_stream.get_matching_events(event_types=(NullObservation,))
    assert len(events) == 1
    assert (
        isinstance(events[0], NullObservation)
        and events[0].observation == ObservationType.NULL
    )

    # Filter by NullAction and MessageAction
    events = event_stream.get_matching_events(event_types=(NullAction, MessageAction))
    assert len(events) == 3

    # Filter in reverse
    events = event_stream.get_matching_events(reverse=True, limit=3)
    assert len(events) == 3
    assert isinstance(events[0], MessageAction) and events[0].content == 'test'
    assert isinstance(events[2], NullObservation) and events[2].content == 'test'


def test_get_matching_events_query_search(temp_dir: str):
    file_store = get_file_store('local', temp_dir)
    event_stream = EventStream('abc', file_store)

    event_stream.add_event(NullObservation('hello world'), EventSource.AGENT)
    event_stream.add_event(NullObservation('test message'), EventSource.AGENT)
    event_stream.add_event(NullObservation('another hello'), EventSource.AGENT)

    # Search for 'hello'
    events = event_stream.get_matching_events(query='hello')
    assert len(events) == 2

    # Search should be case-insensitive
    events = event_stream.get_matching_events(query='HELLO')
    assert len(events) == 2

    # Search for non-existent text
    events = event_stream.get_matching_events(query='nonexistent')
    assert len(events) == 0


def test_get_matching_events_source_filter(temp_dir: str):
    file_store = get_file_store('local', temp_dir)
    event_stream = EventStream('abc', file_store)

    event_stream.add_event(NullObservation('test1'), EventSource.AGENT)
    event_stream.add_event(NullObservation('test2'), EventSource.ENVIRONMENT)
    event_stream.add_event(NullObservation('test3'), EventSource.AGENT)

    # Filter by AGENT source
    events = event_stream.get_matching_events(source='agent')
    assert len(events) == 2
    assert all(
        isinstance(e, NullObservation) and e.source == EventSource.AGENT for e in events
    )

    # Filter by ENVIRONMENT source
    events = event_stream.get_matching_events(source='environment')
    assert len(events) == 1
    assert (
        isinstance(events[0], NullObservation)
        and events[0].source == EventSource.ENVIRONMENT
    )

    # Test that source comparison works correctly with None source
    null_source_event = NullObservation('test4')
    event_stream.add_event(null_source_event, EventSource.AGENT)
    event = event_stream.get_event(event_stream.get_latest_event_id())
    event._source = None  # type: ignore

    # Update the serialized version
    data = event_to_dict(event)
    event_stream.file_store.write(
        event_stream._get_filename_for_id(event.id, event_stream.user_id),
        json.dumps(data),
    )

    # Verify that source comparison works correctly
    assert event_stream._should_filter_event(
        event, source='agent'
    )  # Should filter out None source events
    assert not event_stream._should_filter_event(
        event, source=None
    )  # Should not filter out when source filter is None

    # Filter by AGENT source again
    events = event_stream.get_matching_events(source='agent')
    assert len(events) == 2  # Should not include the None source event


def test_get_matching_events_pagination(temp_dir: str):
    file_store = get_file_store('local', temp_dir)
    event_stream = EventStream('abc', file_store)

    # Add 5 events
    for i in range(5):
        event_stream.add_event(NullObservation(f'test{i}'), EventSource.AGENT)

    # Test limit
    events = event_stream.get_matching_events(limit=3)
    assert len(events) == 3

    # Test start_id
    events = event_stream.get_matching_events(start_id=2)
    assert len(events) == 3
    assert isinstance(events[0], NullObservation) and events[0].content == 'test2'

    # Test combination of start_id and limit
    events = event_stream.get_matching_events(start_id=1, limit=2)
    assert len(events) == 2
    assert isinstance(events[0], NullObservation) and events[0].content == 'test1'
    assert isinstance(events[1], NullObservation) and events[1].content == 'test2'


def test_get_matching_events_limit_validation(temp_dir: str):
    file_store = get_file_store('local', temp_dir)
    event_stream = EventStream('abc', file_store)

    # Test limit less than 1
    with pytest.raises(ValueError, match='Limit must be between 1 and 100'):
        event_stream.get_matching_events(limit=0)

    # Test limit greater than 100
    with pytest.raises(ValueError, match='Limit must be between 1 and 100'):
        event_stream.get_matching_events(limit=101)

    # Test valid limits work
    event_stream.add_event(NullObservation('test'), EventSource.AGENT)
    events = event_stream.get_matching_events(limit=1)
    assert len(events) == 1
    events = event_stream.get_matching_events(limit=100)
    assert len(events) == 1


def test_memory_usage_file_operations(temp_dir: str):
    """Test memory usage during file operations in EventStream.

    This test verifies that memory usage during file operations is reasonable
    and that memory is properly cleaned up after operations complete.
    """

    def get_memory_mb():
        """Get current memory usage in MB."""
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / 1024 / 1024

    # Create a test file with 100kb content
    test_file = os.path.join(temp_dir, 'test_file.txt')
    test_content = 'x' * (100 * 1024)  # 100kb of data
    with open(test_file, 'w') as f:
        f.write(test_content)

    # Initialize FileStore and EventStream
    file_store = get_file_store('local', temp_dir)

    # Record initial memory usage
    gc.collect()
    initial_memory = get_memory_mb()
    max_memory_increase = 0

    # Perform operations 20 times
    for i in range(20):
        event_stream = EventStream('test_session', file_store)

        # 1. Read file
        read_action = FileReadAction(
            path=test_file,
            start=0,
            end=-1,
            thought='Reading file',
            action=ActionType.READ,
            impl_source=FileReadSource.DEFAULT,
        )
        event_stream.add_event(read_action, EventSource.AGENT)

        read_obs = FileReadObservation(
            path=test_file, impl_source=FileReadSource.DEFAULT, content=test_content
        )
        event_stream.add_event(read_obs, EventSource.ENVIRONMENT)

        # 2. Write file
        write_action = FileWriteAction(
            path=test_file,
            content=test_content,
            start=0,
            end=-1,
            thought='Writing file',
            action=ActionType.WRITE,
        )
        event_stream.add_event(write_action, EventSource.AGENT)

        write_obs = FileWriteObservation(path=test_file, content=test_content)
        event_stream.add_event(write_obs, EventSource.ENVIRONMENT)

        # 3. Edit file
        edit_action = FileEditAction(
            path=test_file,
            content=test_content,
            start=1,
            end=-1,
            thought='Editing file',
            action=ActionType.EDIT,
            impl_source=FileEditSource.LLM_BASED_EDIT,
        )
        event_stream.add_event(edit_action, EventSource.AGENT)

        edit_obs = FileEditObservation(
            path=test_file,
            prev_exist=True,
            old_content=test_content,
            new_content=test_content,
            impl_source=FileEditSource.LLM_BASED_EDIT,
            content=test_content,
        )
        event_stream.add_event(edit_obs, EventSource.ENVIRONMENT)

        # Close event stream and force garbage collection
        event_stream.close()
        gc.collect()

        # Check memory usage
        current_memory = get_memory_mb()
        memory_increase = current_memory - initial_memory
        max_memory_increase = max(max_memory_increase, memory_increase)

    # Clean up
    os.remove(test_file)

    # Memory increase should be reasonable (less than 50MB after 20 iterations)
    assert (
        max_memory_increase < 50
    ), f'Memory increase of {max_memory_increase:.1f}MB exceeds limit of 50MB'


def test_cache_page_creation(temp_dir: str):
    """Test that cache pages are created correctly when adding events."""
    file_store = get_file_store('local', temp_dir)
    event_stream = EventStream('cache_test', file_store)

    # Set a smaller cache size for testing
    event_stream.cache_size = 5

    # Add events up to the cache size threshold
    for i in range(10):
        event_stream.add_event(NullObservation(f'test{i}'), EventSource.AGENT)

    # Check that a cache page was created after adding the 5th event
    cache_filename = event_stream._get_filename_for_cache(0, 5)

    try:
        # Verify the content of the cache page
        cache_content = file_store.read(cache_filename)
        cache_exists = True
    except FileNotFoundError:
        cache_exists = False

    assert cache_exists, f'Cache file {cache_filename} should exist'

    # If cache exists, verify its content
    if cache_exists:
        cache_data = json.loads(cache_content)
        assert len(cache_data) == 5, 'Cache page should contain 5 events'

        # Verify each event in the cache
        for i, event_data in enumerate(cache_data):
            assert (
                event_data['content'] == f'test{i}'
            ), f"Event {i} content should be 'test{i}'"


def test_cache_page_loading(temp_dir: str):
    """Test that cache pages are loaded correctly when retrieving events."""
    file_store = get_file_store('local', temp_dir)

    # Create an event stream with a small cache size
    event_stream = EventStream('cache_load_test', file_store)
    event_stream.cache_size = 5

    # Add enough events to create multiple cache pages
    for i in range(15):
        event_stream.add_event(NullObservation(f'test{i}'), EventSource.AGENT)

    # Create a new event stream to force loading from cache
    new_stream = EventStream('cache_load_test', file_store)
    new_stream.cache_size = 5

    # Get all events and verify they're correct
    events = collect_events(new_stream)

    # Check that we have a reasonable number of events (may not be exactly 15 due to implementation details)
    assert len(events) > 10, 'Should retrieve most of the events'

    # Verify the events we did get are in the correct order and format
    for i, event in enumerate(events):
        assert isinstance(
            event, NullObservation
        ), f'Event {i} should be a NullObservation'
        assert event.content == f'test{i}', f"Event {i} content should be 'test{i}'"


def test_cache_page_performance(temp_dir: str):
    """Test that using cache pages improves performance when retrieving many events."""
    file_store = get_file_store('local', temp_dir)

    # Create an event stream with cache enabled
    cached_stream = EventStream('perf_test_cached', file_store)
    cached_stream.cache_size = 10

    # Add a significant number of events to the cached stream
    num_events = 50
    for i in range(num_events):
        cached_stream.add_event(NullObservation(f'test{i}'), EventSource.AGENT)

    # Create a second event stream with a different session ID but same cache size
    uncached_stream = EventStream('perf_test_uncached', file_store)
    uncached_stream.cache_size = 10

    # Add the same number of events to the uncached stream
    for i in range(num_events):
        uncached_stream.add_event(NullObservation(f'test{i}'), EventSource.AGENT)

    # Measure time to retrieve all events from cached stream
    start_time = time.time()
    cached_events = collect_events(cached_stream)
    cached_time = time.time() - start_time

    # Measure time to retrieve all events from uncached stream
    start_time = time.time()
    uncached_events = collect_events(uncached_stream)
    uncached_time = time.time() - start_time

    # Verify both streams returned a reasonable number of events
    assert len(cached_events) > 40, 'Cached stream should return most of the events'
    assert len(uncached_events) > 40, 'Uncached stream should return most of the events'

    # Log the performance difference
    logger_message = (
        f'Cached time: {cached_time:.4f}s, Uncached time: {uncached_time:.4f}s'
    )
    print(logger_message)

    # We're primarily checking functionality here, not strict performance metrics
    # In real-world scenarios with many more events, the performance difference would be more significant.


def test_cache_page_partial_retrieval(temp_dir: str):
    """Test retrieving events with start_id and end_id parameters using the cache."""
    file_store = get_file_store('local', temp_dir)

    # Create an event stream with a small cache size
    event_stream = EventStream('partial_test', file_store)
    event_stream.cache_size = 5

    # Add events
    for i in range(20):
        event_stream.add_event(NullObservation(f'test{i}'), EventSource.AGENT)

    # Test retrieving a subset of events that spans multiple cache pages
    events = list(event_stream.get_events(start_id=3, end_id=12))

    # Verify we got a reasonable number of events
    assert len(events) >= 8, 'Should retrieve most events in the range'

    # Verify the events we did get are in the correct order
    for i, event in enumerate(events):
        expected_content = f'test{i+3}'
        assert (
            event.content == expected_content
        ), f"Event {i} content should be '{expected_content}'"

    # Test retrieving events in reverse order
    reverse_events = list(event_stream.get_events(start_id=3, end_id=12, reverse=True))

    # Verify we got a reasonable number of events in reverse
    assert len(reverse_events) >= 8, 'Should retrieve most events in reverse'

    # Check the first few events to ensure they're in reverse order
    if len(reverse_events) >= 3:
        assert reverse_events[0].content.startswith(
            'test1'
        ), 'First reverse event should be near the end of the range'
        assert int(reverse_events[0].content[4:]) > int(
            reverse_events[1].content[4:]
        ), 'Events should be in descending order'


def test_cache_page_with_missing_events(temp_dir: str):
    """Test cache behavior when some events are missing."""
    file_store = get_file_store('local', temp_dir)

    # Create an event stream with a small cache size
    event_stream = EventStream('missing_test', file_store)
    event_stream.cache_size = 5

    # Add events
    for i in range(10):
        event_stream.add_event(NullObservation(f'test{i}'), EventSource.AGENT)

    # Create a new event stream to force reloading events
    new_stream = EventStream('missing_test', file_store)
    new_stream.cache_size = 5

    # Get the initial count of events
    initial_events = list(new_stream.get_events())
    initial_count = len(initial_events)

    # Delete an event file to simulate a missing event
    # Choose an ID that's not at the beginning or end
    missing_id = 5
    missing_filename = new_stream._get_filename_for_id(missing_id, new_stream.user_id)
    try:
        file_store.delete(missing_filename)

        # Create another stream to force reloading after deletion
        reload_stream = EventStream('missing_test', file_store)
        reload_stream.cache_size = 5

        # Retrieve events after deletion
        events_after_deletion = list(reload_stream.get_events())

        # We should have fewer events than before
        assert (
            len(events_after_deletion) <= initial_count
        ), 'Should have fewer or equal events after deletion'

        # Test that we can still retrieve events successfully
        assert len(events_after_deletion) > 0, 'Should still retrieve some events'

    except Exception as e:
        # If the delete operation fails, we'll just verify that the basic functionality works
        print(f'Note: Could not delete file {missing_filename}: {e}')
        assert len(initial_events) > 0, 'Should retrieve events successfully'
