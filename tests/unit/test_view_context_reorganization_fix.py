"""Tests for the fixed View.from_events method with mixed ContextReorganization and Condensation."""

from openhands.events.action import MessageAction
from openhands.events.action.agent import (
    CondensationAction,
    ContextReorganizationAction,
)
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

    # Create a ContextReorganizationAction
    summary = 'Context reorganization summary'
    files = [{'path': '/workspace/test.py'}]
    context_reorg_action = ContextReorganizationAction(summary=summary, files=files)
    setattr(context_reorg_action, '_id', len(initial_events))

    # Create a ContextReorganizationObservation with cause set to the action's ID
    context_reorg = ContextReorganizationObservation(
        content=summary, summary=summary, files=files
    )
    setattr(context_reorg, '_id', len(initial_events) + 1)
    setattr(context_reorg, '_cause', context_reorg_action.id)

    # Events after context reorganization
    post_reorg_events = [
        MessageAction(content='Post-reorganization message 1', wait_for_response=True),
        NullObservation(content=''),
        MessageAction(content='Post-reorganization message 2', wait_for_response=True),
        NullObservation(content=''),
    ]

    # Set IDs for post-reorganization events
    for i, event in enumerate(post_reorg_events):
        setattr(event, '_id', len(initial_events) + 2 + i)

    # Create a CondensationAction that condenses the post-reorganization messages
    condensation = CondensationAction(
        forgotten_event_ids=[
            post_reorg_events[0].id,
            post_reorg_events[1].id,
        ],  # Forget first two post-reorg messages
        summary='Condensed post-reorganization messages',
        summary_offset=1,  # Insert after the context reorganization
    )
    setattr(condensation, '_id', len(initial_events) + 2 + len(post_reorg_events))

    # Final events
    final_events = [
        MessageAction(content='Final message', wait_for_response=True),
    ]
    setattr(
        final_events[0], '_id', len(initial_events) + 2 + len(post_reorg_events) + 1
    )

    # Combine all events
    all_events = (
        initial_events
        + [context_reorg_action, context_reorg]
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

    # Expected view length: 1 (context reorg) + 0 (context reorg action - not included in view) + 1 (condensation summary) + 2 (remaining post-reorg) + 1 (final)
    assert len(view.events) == 5

    # Check that ContextReorganizationObservation is in the view
    context_reorg_obs_found = False
    agent_condensation_found = False

    for event in view.events:
        if isinstance(event, ContextReorganizationObservation):
            context_reorg_obs_found = True
            assert event.summary == summary
            assert event.files == files
        elif isinstance(event, AgentCondensationObservation):
            agent_condensation_found = True
            assert event.content == 'Condensed post-reorganization messages'

    # Verify that all expected event types are found
    assert context_reorg_obs_found, 'ContextReorganizationObservation not found in view'
    assert agent_condensation_found, 'AgentCondensationObservation not found in view'

    # Check that the remaining post-reorg events and final event are in the view
    post_reorg_events_found = 0
    final_event_found = False

    for event in view.events:
        if event.id == post_reorg_events[2].id or event.id == post_reorg_events[3].id:
            post_reorg_events_found += 1
        elif event.id == final_events[0].id:
            final_event_found = True

    assert post_reorg_events_found == 2, 'Not all post-reorganization events were found'
    assert final_event_found, 'Final event not found in view'
