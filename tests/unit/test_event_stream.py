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
