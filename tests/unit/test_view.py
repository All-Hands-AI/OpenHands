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
    assert view.events == []  # All events forgotten and condensation action removed


def test_from_events_condensation_remove_second():
    events: list[Event] = [MessageAction(content=f'Event {i}') for i in range(5)]
    condensation = CondensationAction(forgotten_event_ids=[1])
    events.append(condensation)
    set_ids(events)

    view = View.from_events(events)
    assert (
        view.events == events[:1] + events[2:5]
    )  # Exclude event 1 and the condensation action


def test_from_events_just_summary():
    events: list[Event] = [MessageAction(content=f'Event {i}') for i in range(5)]
    condensation = CondensationAction(
        forgotten_event_ids=[], summary='My Summary', summary_offset=0
    )
    events.append(condensation)
    set_ids(events)
    view = View.from_events(events)
    assert len(view) == 6  # 5 message events + 1 summary observation
    assert isinstance(
        view[0], AgentCondensationObservation
    )  # Summary inserted at offset 0
    assert view[0].content == 'My Summary'


def test_from_events_summary_stays():
    events: list[Event] = [
        MessageAction(content='Event 0'),
        CondensationAction(
            forgotten_event_ids=[], summary='My Summary', summary_offset=1
        ),
        MessageAction(content='Event 1'),
    ]
    set_ids(events)
    view = View.from_events(events)
    assert len(view) == 3  # 2 message events + 1 summary observation
    assert [e.content for e in view] == [
        'Event 0',
        'My Summary',  # Summary inserted at offset 1
        'Event 1',
    ]


def test_no_condensation_action_in_view():
    """Ensure that CondensationAction events are never present in the resulting view."""
    events: list[Event] = [
        MessageAction(content='Event 0'),
        MessageAction(content='Event 1'),
        CondensationAction(forgotten_event_ids=[0]),
        MessageAction(content='Event 2'),
        MessageAction(content='Event 3'),
    ]
    set_ids(events)
    view = View.from_events(events)

    # Check that no CondensationAction is present in the view
    for event in view:
        assert not isinstance(event, CondensationAction), (
            'CondensationAction should not be present in the view'
        )

    # The view should only contain the non-forgotten MessageActions
    assert len(view) == 3  # Event 1, Event 2, Event 3 (Event 0 was forgotten)


def set_ids(events: list[Event]) -> None:
    """Set the IDs of the events in the list to their index."""
    for i, e in enumerate(events):
        e._id = i  # type: ignore
