import logging

import pytest

from opendevin.events.action.agent import AgentSummarizeAction
from opendevin.events.action.files import FileReadAction, FileWriteAction
from opendevin.events.action.message import MessageAction
from opendevin.events.event import EventSource
from opendevin.events.observation.empty import NullObservation
from opendevin.events.observation.files import FileReadObservation, FileWriteObservation
from opendevin.events.stream import EventStream
from opendevin.memory.history import ShortTermHistory


def collect_events(stream):
    return [event for event in stream.get_events()]


logging.basicConfig(level=logging.DEBUG)


@pytest.fixture
def event_stream():
    event_stream = EventStream('asdf0')
    yield event_stream

    # clear after each test
    event_stream.clear()


def test_chatty_history(event_stream: EventStream):
    history = ShortTermHistory()
    history.set_event_stream(event_stream)

    # a chatty test
    message_action_0 = MessageAction(content='Hello', wait_for_response=False)
    message_action_0._source = EventSource.USER
    event_stream.add_event(message_action_0, EventSource.USER)
    message_action_1 = MessageAction(content='Hello to you too', wait_for_response=True)
    message_action_1._source = EventSource.AGENT
    event_stream.add_event(message_action_1, EventSource.AGENT)
    message_action_2 = MessageAction(
        content="Let's make a cool app.", wait_for_response=False
    )
    message_action_2._source = EventSource.USER
    event_stream.add_event(message_action_2, EventSource.USER)
    read_action = FileReadAction(path='file1.txt')
    event_stream.add_event(read_action, EventSource.USER)

    # in between file read action and observation
    message_action_unknown = MessageAction(content='Wait!', wait_for_response=False)
    message_action_unknown._source = EventSource.USER
    event_stream.add_event(message_action_unknown, EventSource.USER)

    read_observation = FileReadObservation(path='file1.txt', content='File 1 content')
    read_observation._cause = read_action._id
    event_stream.add_event(read_observation, EventSource.AGENT)

    # everyone is chatty
    message_action_3 = MessageAction(content="I'm ready!", wait_for_response=True)
    message_action_3._source = EventSource.AGENT
    event_stream.add_event(message_action_3, EventSource.AGENT)
    message_action_4 = MessageAction(
        content="Great! Let's get started.", wait_for_response=False
    )
    message_action_4._source = EventSource.USER
    event_stream.add_event(message_action_4, EventSource.USER)
    write_action = FileWriteAction(path='file2.txt', content='File 2 content')
    event_stream.add_event(write_action, EventSource.USER)
    write_observation = FileWriteObservation(path='file2.txt', content='File 2 content')
    write_observation._cause = write_action._id
    event_stream.add_event(write_observation, EventSource.AGENT)

    assert len(collect_events(history)) == 10


def test_history_get_events(event_stream: EventStream):
    history = ShortTermHistory()
    history.set_event_stream(event_stream)

    read_action = FileReadAction(path='file1.txt')
    event_stream.add_event(read_action, EventSource.USER)
    read_observation = FileReadObservation(path='file1.txt', content='File 1 content')
    read_observation._cause = read_action._id
    event_stream.add_event(read_observation, EventSource.AGENT)
    write_action = FileWriteAction(path='file2.txt', content='File 2 content')
    event_stream.add_event(write_action, EventSource.USER)
    write_observation = FileWriteObservation(path='file2.txt', content='File 2 content')
    write_observation._cause = write_action._id
    event_stream.add_event(write_observation, EventSource.AGENT)

    events = history.get_events_as_list()

    assert len(events) == 4
    assert isinstance(events[0], FileReadAction)
    assert isinstance(events[1], FileReadObservation)
    assert isinstance(events[2], FileWriteAction)
    assert isinstance(events[3], FileWriteObservation)


def test_history_get_tuples(event_stream: EventStream):
    history = ShortTermHistory()
    history.set_event_stream(event_stream)

    read_action = FileReadAction(path='file1.txt')
    event_stream.add_event(read_action, EventSource.USER)
    read_observation = FileReadObservation(path='file1.txt', content='File 1 content')
    read_observation._cause = read_action._id
    event_stream.add_event(read_observation, EventSource.AGENT)
    # 2 events

    write_action = FileWriteAction(path='file2.txt', content='File 2 content')
    event_stream.add_event(write_action, EventSource.USER)
    write_observation = FileWriteObservation(path='file2.txt', content='File 2 content')
    write_observation._cause = write_action._id
    event_stream.add_event(write_observation, EventSource.AGENT)
    # 4 events

    tuples = history.get_tuples()

    assert len(tuples) == 2
    assert isinstance(tuples[0][0], FileReadAction)
    assert isinstance(tuples[0][1], FileReadObservation)
    assert isinstance(tuples[1][0], FileWriteAction)
    assert isinstance(tuples[1][1], FileWriteObservation)

    events = history.get_events_as_list()
    assert len(events) == 4
    assert isinstance(events[0], FileReadAction)
    assert isinstance(events[1], FileReadObservation)
    assert isinstance(events[2], FileWriteAction)
    assert isinstance(events[3], FileWriteObservation)


def test_history_iterate_tuples(event_stream: EventStream):
    history = ShortTermHistory()
    history.set_event_stream(event_stream)

    read_action = FileReadAction(path='file1.txt')
    event_stream.add_event(read_action, EventSource.USER)
    read_observation = FileReadObservation(path='file1.txt', content='File 1 content')
    read_observation._cause = read_action._id
    event_stream.add_event(read_observation, EventSource.AGENT)
    # 2 events

    message_action = MessageAction(content='Done', wait_for_response=False)
    message_action._source = EventSource.USER
    event_stream.add_event(message_action, EventSource.USER)
    message_action_1 = MessageAction(content='Done', wait_for_response=False)
    message_action_1._source = EventSource.USER
    event_stream.add_event(message_action_1, EventSource.USER)
    write_action = FileWriteAction(path='file2.txt', content='File 2 content')
    event_stream.add_event(write_action, EventSource.USER)
    write_observation = FileWriteObservation(path='file2.txt', content='File 2 content')
    write_observation._cause = write_action._id
    event_stream.add_event(write_observation, EventSource.AGENT)
    # 6 events, among which 2 messages

    tuples = history.get_tuples()

    assert len(tuples) == 4
    assert isinstance(tuples[0][0], FileReadAction)
    assert isinstance(tuples[0][1], FileReadObservation)
    assert isinstance(tuples[1][0], MessageAction)
    assert isinstance(tuples[1][1], NullObservation)
    assert isinstance(tuples[2][0], MessageAction)
    assert isinstance(tuples[2][1], NullObservation)
    assert isinstance(tuples[3][0], FileWriteAction)
    assert isinstance(tuples[3][1], FileWriteObservation)


def test_history_with_message_actions(event_stream: EventStream):
    history = ShortTermHistory()
    history.set_event_stream(event_stream)

    message_action_1 = MessageAction(content='Hello', wait_for_response=False)
    message_action_1._source = EventSource.USER
    event_stream.add_event(message_action_1, EventSource.USER)

    message_action_2 = MessageAction(content='Hi there', wait_for_response=True)
    message_action_2._source = EventSource.AGENT
    event_stream.add_event(message_action_2, EventSource.AGENT)

    read_action = FileReadAction(path='file1.txt')
    event_stream.add_event(read_action, EventSource.USER)
    read_observation = FileReadObservation(path='file1.txt', content='File 1 content')
    read_observation._cause = read_action._id
    event_stream.add_event(read_observation, EventSource.AGENT)

    tuples = history.get_tuples()

    assert len(tuples) == 3
    assert isinstance(tuples[0][0], MessageAction)
    assert isinstance(tuples[0][1], NullObservation)
    assert isinstance(tuples[1][0], MessageAction)
    assert isinstance(tuples[1][1], NullObservation)
    assert isinstance(tuples[2][0], FileReadAction)
    assert isinstance(tuples[2][1], FileReadObservation)


def test_history_with_summary(event_stream: EventStream):
    history = ShortTermHistory()
    history.set_event_stream(event_stream)

    message_action_1 = MessageAction(content='Hello', wait_for_response=False)
    message_action_1._source = EventSource.USER
    event_stream.add_event(message_action_1, EventSource.USER)

    message_action_2 = MessageAction(content='Hi there', wait_for_response=True)
    message_action_2._source = EventSource.AGENT
    event_stream.add_event(message_action_2, EventSource.AGENT)

    read_action_1 = FileReadAction(path='file1.txt')
    event_stream.add_event(read_action_1, EventSource.USER)
    read_observation_1 = FileReadObservation(path='file1.txt', content='File 1 content')
    read_observation_1._cause = read_action_1._id
    event_stream.add_event(read_observation_1, EventSource.AGENT)

    read_action_2 = FileReadAction(path='file2.txt')
    event_stream.add_event(read_action_2, EventSource.USER)
    read_observation_2 = FileReadObservation(path='file2.txt', content='File 2 content')
    read_observation_2._cause = read_action_2._id
    event_stream.add_event(read_observation_2, EventSource.AGENT)

    # Create a summary action and observation
    summary_action = AgentSummarizeAction(
        summarized_actions='I tried to read the files',
        summarized_observations='The agent read the contents of file1.txt and file2.txt',
    )
    summary_action._chunk_start = read_action_1._id
    summary_action._chunk_end = read_observation_2._id

    history.add_summary(summary_action)

    events = list(history.get_events())

    assert len(events) == 3
    assert isinstance(events[0], MessageAction)
    assert isinstance(events[1], MessageAction)
    assert isinstance(events[2], AgentSummarizeAction)
