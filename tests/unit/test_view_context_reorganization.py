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

    # Check that the view only contains one event: a ContextReorganizationObservation
    assert len(view.events) == 1
    assert isinstance(view.events[0], ContextReorganizationObservation)
    assert view.events[0].summary == summary
    assert view.events[0].files == files
    assert view.events[0].observation == ObservationType.CONTEXT_REORGANIZATION


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

    # Check that the view contains the ContextReorganizationObservation followed by the events_after
    assert len(view.events) == 1 + len(events_after)

    # First event should be a ContextReorganizationObservation
    assert isinstance(view.events[0], ContextReorganizationObservation)
    assert view.events[0].summary == summary
    assert view.events[0].files == files

    # Subsequent events should match events_after
    for i, event in enumerate(events_after):
        assert view.events[i + 1].id == event.id


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

    # Check that the view contains only the second ContextReorganizationObservation and final_events
    assert len(view.events) == 1 + len(final_events)

    # First event should be the second ContextReorganizationObservation
    assert isinstance(view.events[0], ContextReorganizationObservation)
    assert view.events[0].summary == reorg2.summary
    assert view.events[0].files == reorg2.files

    # Subsequent events should match final_events
    for i, event in enumerate(final_events):
        assert view.events[i + 1].id == event.id
