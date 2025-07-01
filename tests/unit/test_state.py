from unittest.mock import patch

from openhands.controller.state.state import State, TrafficControlState
from openhands.core.schema import AgentState
from openhands.events.event import Event
from openhands.llm.metrics import Metrics
from openhands.storage.memory import InMemoryFileStore


def example_event(index: int) -> Event:
    event = Event()
    event._message = f'Test message {index}'
    event._id = index
    return event


def test_state_view_caching_avoids_unnecessary_rebuilding():
    """Test that the state view caching avoids unnecessarily rebuilding the view when the history hasn't changed."""
    state = State()
    state.history = [example_event(i) for i in range(5)]

    # Build the view once.
    view = state.view

    # Easy way to check that the cache works -- `view` and future calls of
    # `state.view` should be the same object. We'll check that by using the `id`
    # of the view.
    assert id(view) == id(state.view)

    # Add an event to the history. This should produce a different view.
    state.history.append(example_event(100))

    new_view = state.view
    assert id(new_view) != id(view)

    # But once we have the new view once, it should be cached.
    assert id(new_view) == id(state.view)


def test_state_view_cache_not_serialized():
    """Test that the fields used to cache view construction are not serialized when state is saved."""
    state = State()
    state.history = [example_event(i) for i in range(5)]

    # Build the view once.
    view = state.view

    # Serialize the state.
    store = InMemoryFileStore()
    state.save_to_session('test_sid', store, None)
    restored_state = State.restore_from_session('test_sid', store, None)

    # The state usually has the history rebuilt from the event stream -- we'll
    # simulate this by manually setting the state history to the same events.
    restored_state.history = state.history

    restored_view = restored_state.view

    # Since serialization doesn't include the view cache, the restored view will
    # be structurally identical but _not_ the same object.
    assert id(restored_view) != id(view)
    assert restored_view.events == view.events


def test_restore_older_state_version():
    """Test that we can restore from an older state version (before control flags)."""
    # Create a dictionary that mimics the old state format (before control flags)
    state = State(
        session_id='test_old_session',
        iteration=42,
        local_iteration=42,
        max_iterations=100,
        agent_state=AgentState.RUNNING,
        traffic_control_state=TrafficControlState.NORMAL,
        metrics=Metrics(),
        confirmation_mode=False,
    )

    def no_op_getstate(self):
        return self.__dict__

    store = InMemoryFileStore()

    with patch.object(State, '__getstate__', no_op_getstate):
        state.save_to_session('test_old_session', store, None)

    # Now restore it
    restored_state = State.restore_from_session('test_old_session', store, None)

    # Verify that when we store the active fields are populated with the values from the deprecated fields
    assert restored_state.session_id == 'test_old_session'
    assert restored_state.agent_state == AgentState.LOADING
    assert restored_state.resume_state == AgentState.RUNNING
    assert restored_state.iteration_flag.current_value == 42
    assert restored_state.iteration_flag.max_value == 100


def test_save_without_deprecated_fields():
    """Test that we can save state without deprecated fields"""
    # Create a dictionary that mimics the old state format (before control flags)
    state = State(
        session_id='test_old_session',
        iteration=42,
        local_iteration=42,
        max_iterations=100,
        agent_state=AgentState.RUNNING,
        traffic_control_state=TrafficControlState.NORMAL,
        metrics=Metrics(),
        confirmation_mode=False,
    )

    store = InMemoryFileStore()

    state.save_to_session('test_state', store, None)
    restored_state = State.restore_from_session('test_state', store, None)

    # Verify that when we save and restore, the deprecated fields are removed
    # but the new fields maintain the correct values
    assert restored_state.session_id == 'test_old_session'
    assert restored_state.agent_state == AgentState.LOADING
    assert restored_state.resume_state == AgentState.RUNNING
    assert (
        restored_state.iteration_flag.current_value == 0
    )  # The depreciated attrib was not stored, so it did not override existing values on restore
    assert restored_state.iteration_flag.max_value == 100
