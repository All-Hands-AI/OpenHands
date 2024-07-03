import json
import pytest

from opendevin.events import EventSource, EventStream
from opendevin.events.action import NullAction
from opendevin.events.observation import NullObservation

pytestmark = pytest.mark.order


def clear_all_sessions():
    EventStream.clear_all_sessions()


# Call clear_all_sessions at the module level
clear_all_sessions()


@pytest.fixture(autouse=True)
def clear_sessions_before_each_test():
    EventStream.clear_all_sessions()


def collect_events(stream):
    events = list(stream.get_events())
    return events


@pytest.mark.order(1)
@pytest.mark.asyncio
async def test_basic_flow():
    clear_all_sessions()  # Ensure a clean state before the test
    stream = EventStream(
        'abc', reinitialize=False
    )  # Don't reinitialize from file store
    initial_events = collect_events(stream)
    assert (
        len(initial_events) == 0
    ), f'Expected 0 events, but found {len(initial_events)}'

    await stream.add_event(NullAction(), EventSource.AGENT)
    events_after_add = collect_events(stream)
    assert (
        len(events_after_add) == 1
    ), f'Expected 1 event, but found {len(events_after_add)}'


@pytest.mark.order(2)
@pytest.mark.asyncio
async def test_stream_storage():
    sid = 'def'
    stream = EventStream(sid, reinitialize=False)  # Don't reinitialize from file store
    await stream.add_event(NullObservation(''), EventSource.AGENT)
    assert len(collect_events(stream)) == 1
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


@pytest.mark.order(3)
@pytest.mark.asyncio
async def test_rehydration():
    # Clear all sessions before starting the test
    clear_all_sessions()

    # Create and populate stream1
    stream1 = EventStream('es1', reinitialize=False)
    await stream1.add_event(NullObservation('obs1'), EventSource.AGENT)
    await stream1.add_event(NullObservation('obs2'), EventSource.AGENT)
    assert len(collect_events(stream1)) == 2

    # Create and check stream2
    stream2 = EventStream('es2', reinitialize=False)
    assert len(collect_events(stream2)) == 0

    # Reset stream1
    stream1.reset()
    assert len(collect_events(stream1)) == 0

    # Rehydrate stream1
    stream1rehydrated = EventStream('es1', reinitialize=True)
    events = collect_events(stream1rehydrated)
    assert len(events) == 0

    # Add events to rehydrated stream and check
    await stream1rehydrated.add_event(NullObservation('obs3'), EventSource.AGENT)
    events_after_add = collect_events(stream1rehydrated)
    assert len(events_after_add) == 1
