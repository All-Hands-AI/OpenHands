from openhands.events.action.agent import CondensationAction
from openhands.events.action.message import MessageAction
from openhands.events.event import Event
from openhands.events.observation.agent import AgentCondensationObservation
from openhands.memory.view import View


def test_from_events_simple():
    events: list[Event] = [MessageAction(content=f'Event {i}') for i in range(5)]
    set_ids(events)
    view = View.from_events(events)
    assert len(view) == 5
    assert view.events == events


def test_from_events_condensation_remove_all():
    events: list[Event] = [MessageAction(content=f'Event {i}') for i in range(5)]
    condensation = CondensationAction(forgotten_event_ids=[0, 1, 2, 3, 4])
    events.append(condensation)
    set_ids(events)

    view = View.from_events(events)
    assert view.events == [condensation]


def test_from_events_condensation_remove_second():
    events: list[Event] = [MessageAction(content=f'Event {i}') for i in range(5)]
    condensation = CondensationAction(forgotten_event_ids=[1])
    events.append(condensation)
    set_ids(events)

    view = View.from_events(events)
    assert view.events == events[:1] + events[2:]


def test_from_events_just_summary():
    events: list[Event] = [MessageAction(content=f'Event {i}') for i in range(5)]
    condensation = CondensationAction(forgotten_event_ids=[], summary='My Summary')
    events.append(condensation)
    set_ids(events)
    view = View.from_events(events)
    assert len(view) == 7
    assert view[-2] == condensation
    assert isinstance(view[-1], AgentCondensationObservation)
    assert view[-1].message == 'My Summary'


def test_from_events_summary_stays():
    events: list[Event] = [
        MessageAction(content='Event 0'),
        CondensationAction(forgotten_event_ids=[], summary='My Summary'),
        MessageAction(content='Event 1'),
    ]
    set_ids(events)
    view = View.from_events(events)
    assert len(view) == 4
    assert [e.message for e in view] == [
        'Event 0',
        'Summary: My Summary',
        'My Summary',
        'Event 1',
    ]


def set_ids(events: list[Event]) -> None:
    """Set the IDs of the events in the list to their index."""
    for i, e in enumerate(events):
        e._id = i  # type: ignore
