import json

import pytest

from opendevin.events import EventSource, EventStream
from opendevin.events.action import NullAction
from opendevin.events.observation import NullObservation


@pytest.fixture
def event_stream():
    event_stream = EventStream('abc')
    yield event_stream

    # clear after each test
    event_stream.clear()


def collect_events(stream):
    return [event for event in stream.get_events()]


def test_basic_flow(event_stream: EventStream):
    event_stream.add_event(NullAction(), EventSource.AGENT)
    assert len(collect_events(event_stream)) == 1


def test_stream_storage(event_stream: EventStream):
    event_stream.add_event(NullObservation(''), EventSource.AGENT)
    assert len(collect_events(event_stream)) == 1
    content = event_stream._file_store.read('sessions/abc/events/0.json')
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


def test_rehydration(event_stream: EventStream):
    event_stream.add_event(NullObservation('obs1'), EventSource.AGENT)
    event_stream.add_event(NullObservation('obs2'), EventSource.AGENT)
    assert len(collect_events(event_stream)) == 2

    stream2 = EventStream('es2')
    assert len(collect_events(stream2)) == 0

    stream1rehydrated = EventStream('abc')
    events = collect_events(stream1rehydrated)
    assert len(events) == 2
    assert events[0].content == 'obs1'
    assert events[1].content == 'obs2'
