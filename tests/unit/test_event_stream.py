import json

import pytest
from pytest import TempPathFactory

from openhands.events import EventSource, EventStream
from openhands.events.action import (
    NullAction,
)
from openhands.events.observation import NullObservation
from openhands.storage import get_file_store


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
    content = event_stream.file_store.read('sessions/abc/events/0.json')
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

    # Filter by NullAction
    events = event_stream.get_matching_events(event_type='NullAction')
    assert len(events) == 2
    assert all(e['action'] == 'null' for e in events)

    # Filter by NullObservation
    events = event_stream.get_matching_events(event_type='NullObservation')
    assert len(events) == 1
    assert events[0]['observation'] == 'null'


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
    assert all(e['source'] == 'agent' for e in events)

    # Filter by ENVIRONMENT source
    events = event_stream.get_matching_events(source='environment')
    assert len(events) == 1
    assert events[0]['source'] == 'environment'


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
    assert events[0]['content'] == 'test2'

    # Test combination of start_id and limit
    events = event_stream.get_matching_events(start_id=1, limit=2)
    assert len(events) == 2
    assert events[0]['content'] == 'test1'
    assert events[1]['content'] == 'test2'


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
