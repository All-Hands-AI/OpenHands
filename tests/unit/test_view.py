from openhands.events.action.agent import CondensationAction
from openhands.events.action.message import MessageAction
from openhands.events.event import Event
from openhands.events.observation.agent import AgentCondensationObservation
from openhands.memory.view import View


def test_view_preserves_uncondensed_lists() -> None:
    """Tests that the view preserves event lists that don't contain condensation actions."""
    events: list[Event] = [MessageAction(content=f'Event {i}') for i in range(5)]
    set_ids(events)
    view = View.from_events(events)
    assert len(view) == 5
    assert view.events == events


def test_view_forgets_events() -> None:
    """Tests that views drop forgotten events and the condensation actions."""
    events: list[Event] = [
        *[MessageAction(content=f'Event {i}') for i in range(5)],
        CondensationAction(forgotten_event_ids=[0, 1, 2, 3, 4]),
    ]
    set_ids(events)

    view = View.from_events(events)
    assert view.events == []  # All events forgotten and condensation action removed


def test_view_keeps_non_forgotten_events() -> None:
    """Tests that views keep non-forgotten events."""
    for forgotten_event_id in range(5):
        events: list[Event] = [
            *[MessageAction(content=f'Event {i}') for i in range(5)],
            # Instead of forgetting all events like in
            # `test_view_forgets_events`, in this test we only want to forget
            # one of the events. That way we can check that the rest of the
            # events are preserved.
            CondensationAction(forgotten_event_ids=[forgotten_event_id]),
        ]
        set_ids(events)

        view = View.from_events(events)
        assert (
            view.events
            == events[:forgotten_event_id] + events[(forgotten_event_id + 1) : 5]
        )


def test_view_inserts_summary() -> None:
    """Tests that views insert a summary observation at the specified offset."""
    for offset in range(5):
        events: list[Event] = [
            *[MessageAction(content=f'Event {i}') for i in range(5)],
            CondensationAction(
                forgotten_event_ids=[], summary='My Summary', summary_offset=offset
            ),
        ]
        set_ids(events)
        view = View.from_events(events)

        assert len(view) == 6  # 5 message events + 1 summary observation
        for index, event in enumerate(view):
            print(index, event.content)
            if index == offset:
                assert isinstance(event, AgentCondensationObservation)
                assert event.content == 'My Summary'

            # Events before where the summary is inserted will have content
            # matching their index.
            elif index < offset:
                assert isinstance(event, MessageAction)
                assert event.content == f'Event {index}'

            # Events after where the summary is inserted will be offset by one
            # from the original list.
            else:
                assert isinstance(event, MessageAction)
                assert event.content == f'Event {index - 1}'


def test_no_condensation_action_in_view() -> None:
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
        assert not isinstance(event, CondensationAction)

    # The view should only contain the non-forgotten MessageActions
    assert len(view) == 3  # Event 1, Event 2, Event 3 (Event 0 was forgotten)


def set_ids(events: list[Event]) -> None:
    """Set the IDs of the events in the list to their index."""
    for i, e in enumerate(events):
        e._id = i  # type: ignore
