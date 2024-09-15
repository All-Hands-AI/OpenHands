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
