import gc
import json
import os

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
from openhands.storage.locations import get_conversation_event_filename


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
    events = event_stream.get_matching_events(reverse=True, limit=1)
    assert isinstance(events[0], MessageAction) and events[0].content == 'test'


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
