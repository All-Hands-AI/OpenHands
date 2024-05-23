import json

import pytest

from opendevin.events import EventSource, EventStream
from opendevin.events.action import NullAction
from opendevin.events.observation import NullObservation


def collect_events(stream):
    return [event for event in stream.get_events()]


@pytest.mark.asyncio
async def test_basic_flow():
    stream = EventStream('abc')
    await stream.add_event(NullAction(), EventSource.AGENT)
    assert len(collect_events(stream)) == 1


@pytest.mark.asyncio
async def test_stream_storage():
    stream = EventStream('def')
    await stream.add_event(NullObservation(''), EventSource.AGENT)
    assert len(collect_events(stream)) == 1
    content = stream._file_store.read('sessions/def/events/0.json')
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


@pytest.mark.asyncio
async def test_rehydration():
    stream1 = EventStream('es1')
    await stream1.add_event(NullObservation('obs1'), EventSource.AGENT)
    await stream1.add_event(NullObservation('obs2'), EventSource.AGENT)
    assert len(collect_events(stream1)) == 2

    stream2 = EventStream('es2')
    assert len(collect_events(stream2)) == 0

    stream1rehydrated = EventStream('es1')
    events = collect_events(stream1rehydrated)
    assert len(events) == 2
    assert events[0].content == 'obs1'
    assert events[1].content == 'obs2'
