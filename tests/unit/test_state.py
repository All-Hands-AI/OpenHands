import base64
import pickle

from openhands.controller.state.control_flags import IterationControlFlag
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
    # Create a state object that mimics the old format (before control flags)
    old_state = State()
    old_state.session_id = 'test_old_session'
    old_state.iteration = 42
    old_state.local_iteration = 10
    old_state.max_iterations = 100
    old_state.agent_state = AgentState.RUNNING
    old_state.traffic_control_state = TrafficControlState.NORMAL
    old_state.metrics = Metrics()
    old_state.local_metrics = Metrics()
    old_state.delegates = {}

    # Manually pickle and save the old state
    store = InMemoryFileStore()
    pickled = pickle.dumps(old_state)
    encoded = base64.b64encode(pickled).decode('utf-8')
    store.write('test_old_session_state.json', encoded)

    # Restore the state using the current code
    restored_state = State()
    restored_state.__setstate__(old_state.__dict__.copy())

    # Verify that deprecated fields are still present (for backward compatibility)
    assert hasattr(restored_state, 'iteration')
    assert hasattr(restored_state, 'local_iteration')
    assert hasattr(restored_state, 'max_iterations')
    assert hasattr(restored_state, 'traffic_control_state')
    assert hasattr(restored_state, 'local_metrics')
    assert hasattr(restored_state, 'delegates')

    # Verify that new fields are properly initialized
    assert hasattr(restored_state, 'iteration_flag')
    assert isinstance(restored_state.iteration_flag, IterationControlFlag)
    assert (
        restored_state.iteration_flag.current_value == 42
    )  # Should match the old iteration value
    assert (
        restored_state.iteration_flag.max_value == 100
    )  # Should match the old max_iterations value
    assert restored_state.budget_flag is None

    # Test the full restore_from_session method
    # First, save the old state to the file store
    old_state.save_to_session('test_old_session', store, None)

    # Now restore it
    fully_restored_state = State.restore_from_session('test_old_session', store, None)

    # Verify the state was properly restored and converted
    assert fully_restored_state.session_id == 'test_old_session'
    assert hasattr(fully_restored_state, 'iteration')  # Still has old fields
    assert hasattr(fully_restored_state, 'max_iterations')
    assert hasattr(fully_restored_state, 'iteration_flag')  # But also has new fields
    assert fully_restored_state.agent_state == AgentState.LOADING
    assert fully_restored_state.resume_state == AgentState.RUNNING

    # Now test that when we save this state again, the deprecated fields are removed
    serialized_state = fully_restored_state.__getstate__()
    assert 'iteration' not in serialized_state
    assert 'local_iteration' not in serialized_state
    assert 'max_iterations' not in serialized_state
    assert 'traffic_control_state' not in serialized_state
    assert 'local_metrics' not in serialized_state
    assert 'delegates' not in serialized_state
