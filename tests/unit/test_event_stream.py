import asyncio
import json

import pytest

from opendevin.events import EventSource, EventStream
from opendevin.events.action import NullAction
from opendevin.events.observation import NullObservation
from opendevin.runtime.utils.async_utils import async_to_sync


def clear_all_sessions():
    EventStream.clear_all_sessions()


# Call clear_all_sessions at the module level
clear_all_sessions()


@pytest.fixture(autouse=True)
def clear_sessions_before_each_test():
    EventStream.clear_all_sessions()


@pytest.fixture
def event_stream():
    event_stream = EventStream('abc')
    yield event_stream

    # clear after each test
    event_stream.clear()


async def collect_events(stream):
    return await asyncio.to_thread(lambda: list(stream.get_events()))


@pytest.mark.asyncio
async def test_basic_flow():
    clear_all_sessions()  # Ensure a clean state before the test
    stream = EventStream(
        'abc', reinitialize=False
    )  # Don't reinitialize from file store
    initial_events = await collect_events(stream)
    assert (
        len(initial_events) == 0
    ), f'Expected 0 events, but found {len(initial_events)}'

    await stream.add_event(NullAction(), EventSource.AGENT)
    events_after_add = await collect_events(stream)
    assert (
        len(events_after_add) == 1
    ), f'Expected 1 event, but found {len(events_after_add)}'


@pytest.mark.asyncio
async def test_stream_storage():
    sid = 'def'
    stream = EventStream(sid, reinitialize=False)  # Don't reinitialize from file store
    await stream.add_event(NullObservation(''), EventSource.AGENT)
    events = await collect_events(stream)  # Await the coroutine
    assert len(events) == 1
    content = stream._file_store.read(f'sessions/{sid}/events/0.json')
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
async def test_rehydration(event_stream: EventStream):
    # Clear all sessions before starting the test
    clear_all_sessions()

    await event_stream.add_event(NullObservation('obs1'), EventSource.AGENT)
    await event_stream.add_event(NullObservation('obs2'), EventSource.AGENT)
    events = await collect_events(event_stream)  # Await the coroutine
    assert len(events) == 2

    # Create and check stream2
    stream2 = EventStream('es2')
    assert len(await collect_events(stream2)) == 0  # Await the coroutine

    stream1rehydrated = EventStream('abc')
    events = await collect_events(stream1rehydrated)  # Await the coroutine
    assert len(events) == 2
    assert events[0].content == 'obs1'
    assert events[1].content == 'obs2'


# Non-async versions of the tests
def test_basic_flow_sync():
    clear_all_sessions()  # Ensure a clean state before the test
    stream = EventStream(
        'abc', reinitialize=False
    )  # Don't reinitialize from file store
    initial_events = async_to_sync(collect_events)(stream)
    assert (
        len(initial_events) == 0
    ), f'Expected 0 events, but found {len(initial_events)}'

    async_to_sync(stream.add_event)(NullAction(), EventSource.AGENT)
    events_after_add = async_to_sync(collect_events)(stream)
    assert (
        len(events_after_add) == 1
    ), f'Expected 1 event, but found {len(events_after_add)}'


def test_stream_storage_sync():
    sid = 'def'
    stream = EventStream(sid, reinitialize=False)  # Don't reinitialize from file store
    async_to_sync(stream.add_event)(NullObservation(''), EventSource.AGENT)
    events = async_to_sync(collect_events)(stream)
    assert len(events) == 1
    content = stream._file_store.read(f'sessions/{sid}/events/0.json')
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


def test_rehydration_sync(event_stream: EventStream):
    # Clear all sessions before starting the test
    clear_all_sessions()

    async_to_sync(event_stream.add_event)(NullObservation('obs1'), EventSource.AGENT)
    async_to_sync(event_stream.add_event)(NullObservation('obs2'), EventSource.AGENT)
    events = async_to_sync(collect_events)(event_stream)
    assert len(events) == 2

    # Create and check stream2
    stream2 = EventStream('es2')
    assert len(async_to_sync(collect_events)(stream2)) == 0
    stream1rehydrated = EventStream('abc')
    events = async_to_sync(collect_events)(stream1rehydrated)
    assert len(events) == 2
    assert events[0].content == 'obs1'
    assert events[1].content == 'obs2'
