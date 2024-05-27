from opendevin.events.action.action import Action
from opendevin.events.action.files import FileReadAction, FileWriteAction
from opendevin.events.action.message import MessageAction
from opendevin.events.event import EventSource
from opendevin.events.observation.empty import NullObservation
from opendevin.events.observation.files import FileReadObservation, FileWriteObservation
from opendevin.events.observation.observation import Observation
from opendevin.memory.history import ShortTermHistory


def test_history_append_events():
    history = ShortTermHistory()

    # a chatty test
    message_action_0 = MessageAction(content='Hello', wait_for_response=False)
    message_action_0._source = EventSource.USER
    message_action_0._id = 0
    message_action_1 = MessageAction(content='Hello to you too', wait_for_response=True)
    message_action_1._source = EventSource.AGENT
    message_action_1._id = 1
    message_action_2 = MessageAction(
        content="Let's make a cool app.", wait_for_response=False
    )
    message_action_2._source = EventSource.USER
    message_action_2._id = 2
    read_action = FileReadAction(path='file1.txt')
    read_action._id = 3
    message_action_unknown = MessageAction(content='Wait!', wait_for_response=False)
    message_action_unknown._source = EventSource.USER
    message_action_unknown._id = 4
    read_observation = FileReadObservation(path='file1.txt', content='File 1 content')
    read_observation._cause = read_action._id
    message_action_3 = MessageAction(content="I'm ready!", wait_for_response=True)
    message_action_3._source = EventSource.AGENT
    message_action_3._id = 5
    message_action_4 = MessageAction(
        content="Great! Let's get started.", wait_for_response=False
    )
    message_action_4._source = EventSource.USER
    message_action_4._id = 6
    write_action = FileWriteAction(path='file2.txt', content='File 2 content')
    write_action._id = 7
    write_observation = FileWriteObservation(path='file2.txt', content='File 2 content')
    write_observation._cause = write_action._id

    history.append(message_action_0)
    history.append(message_action_1)
    history.append(message_action_2)
    history.append((read_action, read_observation))
    history.append(message_action_unknown)
    history.append(message_action_3)
    history.append(message_action_4)
    history.append((write_action, write_observation))

    assert len(history) == 10
    assert isinstance(history[0], MessageAction)
    assert isinstance(history[1], MessageAction)
    assert isinstance(history[2], MessageAction)
    assert isinstance(history[3], FileReadAction)
    assert isinstance(history[4], FileReadObservation)
    assert isinstance(history[5], MessageAction)
    assert isinstance(history[6], MessageAction)
    assert isinstance(history[7], MessageAction)
    assert isinstance(history[8], FileWriteAction)
    assert isinstance(history[9], FileWriteObservation)


def test_history_get_events():
    history = ShortTermHistory()

    read_action = FileReadAction(path='file1.txt')
    read_action._id = 1
    read_observation = FileReadObservation(path='file1.txt', content='File 1 content')
    read_observation._cause = read_action._id
    write_action = FileWriteAction(path='file2.txt', content='File 2 content')
    write_action._id = 2
    write_observation = FileWriteObservation(path='file2.txt', content='File 2 content')
    write_observation._cause = write_action._id

    history.append((read_action, read_observation))
    history.append((write_action, write_observation))

    events = history.get_events()

    assert len(events) == 4
    assert isinstance(events[0], FileReadAction)
    assert isinstance(events[1], FileReadObservation)
    assert isinstance(events[2], FileWriteAction)
    assert isinstance(events[3], FileWriteObservation)


def test_history_get_tuples():
    history = ShortTermHistory()

    read_action = FileReadAction(path='file1.txt')
    read_action._id = 1
    read_observation = FileReadObservation(path='file1.txt', content='File 1 content')
    read_observation._cause = read_action._id
    write_action = FileWriteAction(path='file2.txt', content='File 2 content')
    write_action._id = 2
    write_observation = FileWriteObservation(path='file2.txt', content='File 2 content')
    write_observation._cause = write_action._id

    history.append((read_action, read_observation))
    history.append((write_action, write_observation))

    tuples = history.get_tuples()

    assert len(tuples) == 2
    assert isinstance(tuples[0][0], FileReadAction)
    assert isinstance(tuples[0][1], FileReadObservation)
    assert isinstance(tuples[1][0], FileWriteAction)
    assert isinstance(tuples[1][1], FileWriteObservation)

    events = history.get_events()
    assert len(events) == 4
    assert isinstance(events[0], FileReadAction)
    assert isinstance(events[1], FileReadObservation)
    assert isinstance(events[2], FileWriteAction)
    assert isinstance(events[3], FileWriteObservation)


def test_history_iterate_tuples():
    history = ShortTermHistory()

    read_action = FileReadAction(path='file1.txt')
    read_action._id = 1
    read_observation = FileReadObservation(path='file1.txt', content='File 1 content')
    read_observation._cause = read_action._id
    message_action = MessageAction(content='Done', wait_for_response=False)
    message_action._source = EventSource.USER
    message_action._id = 2
    message_action_1 = MessageAction(content='Done', wait_for_response=False)
    message_action_1._source = EventSource.USER
    message_action_1._id = 3
    write_action = FileWriteAction(path='file2.txt', content='File 2 content')
    write_action._id = 4
    write_observation = FileWriteObservation(path='file2.txt', content='File 2 content')
    write_observation._cause = write_action._id

    history.append((read_action, read_observation))
    history.append(message_action)
    history.append((write_action, write_observation))

    tuples: list[tuple[Action, Observation]] = []
    for act, obs in history.get_tuples():
        tuples.append((act, obs))

    assert len(tuples) == 4
    assert isinstance(tuples[0][0], FileReadAction)
    assert isinstance(tuples[0][1], FileReadObservation)
    assert isinstance(tuples[1][0], MessageAction)
    assert isinstance(tuples[1][1], NullObservation)
    assert isinstance(tuples[2][0], MessageAction)
    assert isinstance(tuples[2][1], NullObservation)
    assert isinstance(tuples[3][0], FileWriteAction)
    assert isinstance(tuples[3][1], FileWriteObservation)


def test_history_with_message_actions():
    history = ShortTermHistory()

    message_action_1 = MessageAction(content='Hello', wait_for_response=False)
    message_action_1._source = EventSource.USER
    message_action_1._id = 1

    message_action_2 = MessageAction(content='Hi there', wait_for_response=True)
    message_action_2._source = EventSource.AGENT
    message_action_2._id = 2

    read_action = FileReadAction(path='file1.txt')
    read_action._id = 3
    read_observation = FileReadObservation(path='file1.txt', content='File 1 content')
    read_observation._cause = read_action._id

    history.append(message_action_1)
    history.append(message_action_2)
    history.append((read_action, read_observation))

    tuples = history.get_tuples()

    assert len(tuples) == 3
    assert isinstance(tuples[0][0], MessageAction)
    assert isinstance(tuples[0][1], NullObservation)
    assert isinstance(tuples[1][0], MessageAction)
    assert isinstance(tuples[1][1], NullObservation)
    assert isinstance(tuples[2][0], FileReadAction)
    assert isinstance(tuples[2][1], FileReadObservation)
