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

    read_action = FileReadAction(path='file1.txt')
    read_observation = FileReadObservation(path='file1.txt', content='File 1 content')
    write_action = FileWriteAction(path='file2.txt', content='File 2 content')
    write_observation = FileWriteObservation(path='file2.txt', content='File 2 content')

    history.append(read_action)
    read_observation._cause = read_action._id = 1
    history.append(read_observation)
    history.append(write_action)
    write_observation._cause = write_action._id = 2
    history.append(write_observation)

    assert len(history) == 4
    assert isinstance(history[0], FileReadAction)
    assert isinstance(history[1], FileReadObservation)
    assert isinstance(history[2], FileWriteAction)
    assert isinstance(history[3], FileWriteObservation)


def test_history_get_events():
    history = ShortTermHistory()

    read_action = FileReadAction(path='file1.txt')
    read_observation = FileReadObservation(path='file1.txt', content='File 1 content')
    write_action = FileWriteAction(path='file2.txt', content='File 2 content')
    write_observation = FileWriteObservation(path='file2.txt', content='File 2 content')

    history.append(read_action)
    read_observation._cause = read_action._id = 1
    history.append(read_observation)
    history.append(write_action)
    write_observation._cause = write_action._id = 2
    history.append(write_observation)

    events = history.get_events()

    assert len(events) == 4
    assert isinstance(events[0], FileReadAction)
    assert isinstance(events[1], FileReadObservation)
    assert isinstance(events[2], FileWriteAction)
    assert isinstance(events[3], FileWriteObservation)


def test_history_get_tuples():
    history = ShortTermHistory()

    read_action = FileReadAction(path='file1.txt')
    read_observation = FileReadObservation(path='file1.txt', content='File 1 content')
    write_action = FileWriteAction(path='file2.txt', content='File 2 content')
    write_observation = FileWriteObservation(path='file2.txt', content='File 2 content')

    history.append(read_action)
    read_observation._cause = read_action._id = 1
    history.append(read_observation)
    history.append(write_action)
    write_observation._cause = write_action._id = 2
    history.append(write_observation)

    tuples = history.get_tuples()

    assert len(tuples) == 2
    assert isinstance(tuples[0][0], FileReadAction)
    assert isinstance(tuples[0][1], FileReadObservation)
    assert isinstance(tuples[1][0], FileWriteAction)
    assert isinstance(tuples[1][1], FileWriteObservation)


def test_history_iterate_tuples():
    history = ShortTermHistory()

    read_action = FileReadAction(path='file1.txt')
    read_observation = FileReadObservation(path='file1.txt', content='File 1 content')
    message_action = MessageAction(content='Done', wait_for_response=False)
    message_action._source = EventSource.USER
    write_action = FileWriteAction(path='file2.txt', content='File 2 content')
    write_observation = FileWriteObservation(path='file2.txt', content='File 2 content')

    history.append(read_action)
    read_observation._cause = read_action._id = 1
    history.append(read_observation)
    history.append(message_action)
    history.append(write_action)
    write_observation._cause = write_action._id = 2
    history.append(write_observation)

    tuples: list[tuple[Action, Observation]] = []
    for act, obs in history.get_tuples():
        tuples.append((act, obs))

    assert len(tuples) == 3
    assert isinstance(tuples[0][0], FileReadAction)
    assert isinstance(tuples[0][1], FileReadObservation)
    assert isinstance(tuples[1][0], MessageAction)
    assert isinstance(tuples[1][1], NullObservation)
    assert isinstance(tuples[2][0], FileWriteAction)
    assert isinstance(tuples[2][1], FileWriteObservation)
