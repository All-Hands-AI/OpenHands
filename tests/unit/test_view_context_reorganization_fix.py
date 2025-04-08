"""Tests for the fixed View.from_events method with mixed ContextReorganization and Condensation."""

from openhands.events.action import MessageAction
from openhands.events.action.agent import CondensationAction
from openhands.events.observation import NullObservation
from openhands.events.observation.agent import AgentCondensationObservation
from openhands.events.observation.context_reorganization import (
    ContextReorganizationObservation,
)
from openhands.memory.view import View


def test_context_reorganization_followed_by_condensation_fixed():
    """Test that View correctly handles a ContextReorganization followed by a Condensation."""
    # Create initial events
    initial_events = [
        MessageAction(content='Initial message 1', wait_for_response=True),
        NullObservation(content=''),
        MessageAction(content='Initial message 2', wait_for_response=True),
        NullObservation(content=''),
    ]

    # Set IDs for initial events
    for i, event in enumerate(initial_events):
        setattr(event, '_id', i)

    # Create a ContextReorganizationObservation
    summary = 'Context reorganization summary'
    files = [{'path': '/workspace/test.py'}]
    context_reorg = ContextReorganizationObservation(
        content=summary, summary=summary, files=files
    )
    setattr(context_reorg, '_id', len(initial_events))

    # Events after context reorganization
    post_reorg_events = [
        MessageAction(content='Post-reorganization message 1', wait_for_response=True),
        NullObservation(content=''),
        MessageAction(content='Post-reorganization message 2', wait_for_response=True),
        NullObservation(content=''),
    ]

    # Set IDs for post-reorganization events
    for i, event in enumerate(post_reorg_events):
        setattr(event, '_id', len(initial_events) + 1 + i)

    # Create a CondensationAction that condenses the post-reorganization messages
    condensation = CondensationAction(
        forgotten_event_ids=[
            post_reorg_events[0].id,
            post_reorg_events[1].id,
        ],  # Forget first two post-reorg messages
        summary='Condensed post-reorganization messages',
        summary_offset=1,  # Insert after the context reorganization
    )
    setattr(condensation, '_id', len(initial_events) + 1 + len(post_reorg_events))

    # Final events
    final_events = [
        MessageAction(content='Final message', wait_for_response=True),
    ]
    setattr(
        final_events[0], '_id', len(initial_events) + 1 + len(post_reorg_events) + 1
    )

    # Combine all events
    all_events = (
        initial_events
        + [context_reorg]
        + post_reorg_events
        + [condensation]
        + final_events
    )

    # Create a view from the events
    view = View.from_events(all_events)

    # The expected behavior is:
    # 1. ContextReorganizationObservation replaces all events before it
    # 2. CondensationAction affects events after the ContextReorganizationObservation
    # 3. The resulting view should contain:
    #    - ContextReorganizationObservation
    #    - AgentCondensationObservation (from the CondensationAction)
    #    - Remaining post-reorg events (not forgotten)
    #    - Final events

    # Expected view length: 1 (context reorg) + 1 (condensation summary) + 2 (remaining post-reorg) + 1 (final)
    assert len(view.events) == 5

    # First event should be the ContextReorganizationObservation
    assert isinstance(view.events[0], ContextReorganizationObservation)
    assert view.events[0].summary == summary
    assert view.events[0].files == files

    # Second event should be the AgentCondensationObservation
    assert isinstance(view.events[1], AgentCondensationObservation)
    assert view.events[1].content == 'Condensed post-reorganization messages'

    # Third and fourth events should be the remaining post-reorg events
    assert view.events[2].id == post_reorg_events[2].id
    assert view.events[3].id == post_reorg_events[3].id

    # Fifth event should be the final event
    assert view.events[4].id == final_events[0].id
