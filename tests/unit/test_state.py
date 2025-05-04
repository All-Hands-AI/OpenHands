from openhands.controller.state.state import State
from openhands.events.event import Event
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
