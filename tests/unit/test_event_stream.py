import pytest

from opendevin.events.action import NullAction
from opendevin.events.stream import EventSource, EventStream


@pytest.mark.asyncio
async def test_basic_flow():
    stream = EventStream('abc')
    await stream.add_event(NullAction(), EventSource.AGENT)
    assert len(stream._events) == 1
