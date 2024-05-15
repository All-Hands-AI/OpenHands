import json

import pytest

from opendevin.events.action import NullAction
from opendevin.events.observation import NullObservation
from opendevin.events.stream import EventSource, EventStream


@pytest.mark.asyncio
async def test_basic_flow():
    stream = EventStream('abc')
    await stream.add_event(NullAction(), EventSource.AGENT)
    assert len(stream._events) == 1


@pytest.mark.asyncio
async def test_stream_storage():
    stream = EventStream('def')
    await stream.add_event(NullObservation(''), EventSource.AGENT)
    assert len(stream._events) == 1
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
    assert len(stream1._events) == 2

    stream2 = EventStream('es2')
    assert len(stream2._events) == 0
    await stream2._rehydrate()
    assert len(stream2._events) == 0

    stream1rehydrated = EventStream('es1')
    assert len(stream1rehydrated._events) == 0
    await stream1rehydrated._rehydrate()
    assert len(stream1rehydrated._events) == 2
    assert stream1rehydrated._events[0].content == 'obs1'
    assert stream1rehydrated._events[1].content == 'obs2'
