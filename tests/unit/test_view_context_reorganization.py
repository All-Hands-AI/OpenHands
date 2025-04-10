"""Tests for the View.from_events method with ContextReorganizationObservation."""

from openhands.core.schema import ObservationType
from openhands.events.action import MessageAction
from openhands.events.observation import NullObservation
from openhands.events.observation.context_reorganization import (
    ContextReorganizationObservation,
)
from openhands.memory.view import View


def test_context_reorganization_replaces_previous_events():
    """Test that ContextReorganizationObservation replaces all previous events with a single observation."""
    # Create a series of events
    events = [
        MessageAction(content='Hello', wait_for_response=True),
        NullObservation(content=''),
        MessageAction(content='How are you?', wait_for_response=True),
        NullObservation(content=''),
    ]

    # Create a ContextReorganizationObservation
    summary = 'User greeted the assistant and asked how it was doing. Assistant responded positively.'
    files = [{'path': '/workspace/test.py'}]
    context_reorganization = ContextReorganizationObservation(
        content=summary, summary=summary, files=files
    )

    # Add the ContextReorganizationObservation to the events
    all_events = events + [context_reorganization]

    # Create a view from the events
    view = View.from_events(all_events)

    # Check that the view contains the ContextReorganizationObservation
    assert len(view.events) == 5

    # Find the ContextReorganizationObservation in the view
    context_reorg_found = False
    for event in view.events:
        if isinstance(event, ContextReorganizationObservation):
            context_reorg_found = True
            assert event.summary == summary
            assert event.files == files
            assert event.observation == ObservationType.CONTEXT_REORGANIZATION

    assert context_reorg_found, 'ContextReorganizationObservation not found in view'


def test_context_reorganization_preserves_subsequent_events():
    """Test that ContextReorganizationObservation preserves events that come after it."""
    # Create a series of events
    events_before = [
        MessageAction(content='Hello', wait_for_response=True),
        NullObservation(content=''),
    ]

    # Create a ContextReorganizationObservation
    summary = 'User greeted the assistant.'
    files = [{'path': '/workspace/test.py'}]
    context_reorganization = ContextReorganizationObservation(
        content=summary, summary=summary, files=files
    )

    # Create events that come after the ContextReorganizationObservation
    events_after = [
        MessageAction(content='How are you?', wait_for_response=True),
        NullObservation(content=''),
    ]

    # Combine all events
    all_events = events_before + [context_reorganization] + events_after

    # Create a view from the events
    view = View.from_events(all_events)

    # Check that the view contains the ContextReorganizationObservation and the events_after
    assert len(view.events) == 5

    # Find the ContextReorganizationObservation in the view
    context_reorg_found = False
    for event in view.events:
        if isinstance(event, ContextReorganizationObservation):
            context_reorg_found = True
            assert event.summary == summary
            assert event.files == files

    assert context_reorg_found, 'ContextReorganizationObservation not found in view'

    # Check that events_after are in the view
    for event in events_after:
        found = False
        for view_event in view.events:
            if (
                hasattr(view_event, 'id')
                and hasattr(event, 'id')
                and view_event.id == event.id
            ):
                found = True
                break
        assert found, f'Event with id {event.id} not found in view'


def test_multiple_context_reorganizations():
    """Test that multiple ContextReorganizationObservations work correctly."""
    # Create initial events
    initial_events = [
        MessageAction(content='Hello', wait_for_response=True),
        NullObservation(content=''),
    ]

    # First reorganization
    reorg1 = ContextReorganizationObservation(
        content='Initial greeting',
        summary='Initial greeting',
        files=[{'path': '/workspace/test1.py'}],
    )

    # Events after first reorganization
    middle_events = [
        MessageAction(content='How are you?', wait_for_response=True),
        NullObservation(content=''),
    ]

    # Second reorganization
    reorg2 = ContextReorganizationObservation(
        content='Full conversation summary',
        summary='Full conversation summary',
        files=[{'path': '/workspace/test1.py'}, {'path': '/workspace/test2.py'}],
    )

    # Final events
    final_events = [
        MessageAction(content='Great!', wait_for_response=True),
    ]

    # Combine all events
    all_events = initial_events + [reorg1] + middle_events + [reorg2] + final_events

    # Create a view from the events
    view = View.from_events(all_events)

    # Check that the view contains the second ContextReorganizationObservation and final_events
    assert len(view.events) == 7

    # Find the second ContextReorganizationObservation in the view
    reorg2_found = False
    for event in view.events:
        if (
            isinstance(event, ContextReorganizationObservation)
            and event.summary == reorg2.summary
        ):
            reorg2_found = True
            assert event.files == reorg2.files

    assert reorg2_found, 'Second ContextReorganizationObservation not found in view'

    # Check that final_events are in the view
    for event in final_events:
        found = False
        for view_event in view.events:
            if (
                hasattr(view_event, 'id')
                and hasattr(event, 'id')
                and view_event.id == event.id
            ):
                found = True
                break
        assert found, f'Event with id {event.id} not found in view'
