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
    print(stream._file_store.list(''))
    content = stream._file_store.read('sessions/def/events/1.json')
    assert content is not None
    assert content == '{}'
