import asyncio
from unittest.mock import MagicMock

import pytest

from openhands.controller.agent_controller import AgentController
from openhands.events import EventSource
from openhands.events.action import CmdRunAction, MessageAction
from openhands.events.observation import CmdOutputObservation


@pytest.fixture
def mock_event_stream():
    stream = MagicMock()
    # Mock get_events to return an empty list by default
    stream.get_events.return_value = []
    # Mock get_latest_event_id to return a valid integer
    stream.get_latest_event_id.return_value = 0
    return stream


@pytest.fixture
def mock_agent():
    agent = MagicMock()
    agent.llm = MagicMock()
    agent.llm.config = MagicMock()
    # Set max_message_chars to a specific value to avoid comparison issues
    agent.llm.config.max_message_chars = 1000
    agent.llm.metrics = MagicMock()
    return agent


class TestTruncation:
    def test_apply_conversation_window_basic(self, mock_event_stream, mock_agent):
        controller = AgentController(
            agent=mock_agent,
            event_stream=mock_event_stream,
            max_iterations=10,
            sid='test_truncation',
            confirmation_mode=False,
            headless_mode=True,
        )

        # Create a sequence of events with IDs
        first_msg = MessageAction(content='Hello, start task', wait_for_response=False)
        first_msg._source = EventSource.USER
        first_msg._id = 1

        cmd1 = CmdRunAction(command='ls')
        cmd1._id = 2
        obs1 = CmdOutputObservation(command='ls', content='file1.txt', command_id=2)
        obs1._id = 3
        obs1._cause = 2

        cmd2 = CmdRunAction(command='pwd')
        cmd2._id = 4
        obs2 = CmdOutputObservation(command='pwd', content='/home', command_id=4)
        obs2._id = 5
        obs2._cause = 4

        events = [first_msg, cmd1, obs1, cmd2, obs2]

        # Apply truncation
        truncated = controller._apply_conversation_window(events)

        # Should keep first user message and roughly half of other events
        assert (
            len(truncated) >= 3
        )  # First message + at least one action-observation pair
        assert truncated[0] == first_msg  # First message always preserved
        assert controller.state.start_id == first_msg._id
        assert controller.state.truncation_id is not None

        # Verify pairs aren't split
        for i, event in enumerate(truncated[1:]):
            if isinstance(event, CmdOutputObservation):
                assert any(e._id == event._cause for e in truncated[: i + 1])

    def test_truncation_does_not_impact_trajectory(self, mock_event_stream, mock_agent):
        controller = AgentController(
            agent=mock_agent,
            event_stream=mock_event_stream,
            max_iterations=10,
            sid='test_truncation',
            confirmation_mode=False,
            headless_mode=True,
        )

        # Create a sequence of events with IDs
        first_msg = MessageAction(content='Hello, start task', wait_for_response=False)
        first_msg._source = EventSource.USER
        first_msg._id = 1

        pairs = 10
        history_len = 1 + 2 * pairs
        events = [first_msg]
        for i in range(pairs):
            cmd = CmdRunAction(command=f'cmd{i}')
            cmd._id = i + 2
            obs = CmdOutputObservation(
                command=f'cmd{i}', content=f'output{i}', command_id=cmd._id
            )
            obs._cause = cmd._id
            events.extend([cmd, obs])

        # patch events to history for testing purpose
        controller.state.history = events

        # Update mock event stream
        mock_event_stream.get_events.return_value = controller.state.history

        assert len(controller.state.history) == history_len

        # Force apply truncation
        controller._handle_long_context_error()

        # Check that the history has been truncated before closing the controller
        assert len(controller.state.history) == 13 < history_len

        # Check that after properly closing the controller, history is recovered
        asyncio.run(controller.close())
        assert len(controller.event_stream.get_events()) == history_len
        assert len(controller.state.history) == history_len
        assert len(controller.get_trajectory()) == history_len

    def test_context_window_exceeded_handling(self, mock_event_stream, mock_agent):
        controller = AgentController(
            agent=mock_agent,
            event_stream=mock_event_stream,
            max_iterations=10,
            sid='test_truncation',
            confirmation_mode=False,
            headless_mode=True,
        )

        # Setup initial history with IDs
        first_msg = MessageAction(content='Start task', wait_for_response=False)
        first_msg._source = EventSource.USER
        first_msg._id = 1

        # Add agent question
        agent_msg = MessageAction(
            content='What task would you like me to perform?', wait_for_response=True
        )
        agent_msg._source = EventSource.AGENT
        agent_msg._id = 2

        # Add user response
        user_response = MessageAction(
            content='Please list all files and show me current directory',
            wait_for_response=False,
        )
        user_response._source = EventSource.USER
        user_response._id = 3

        cmd1 = CmdRunAction(command='ls')
        cmd1._id = 4
        obs1 = CmdOutputObservation(command='ls', content='file1.txt', command_id=4)
        obs1._id = 5
        obs1._cause = 4

        # Update mock event stream to include new messages
        mock_event_stream.get_events.return_value = [
            first_msg,
            agent_msg,
            user_response,
            cmd1,
            obs1,
        ]
        controller.state.history = [first_msg, agent_msg, user_response, cmd1, obs1]
        original_history_len = len(controller.state.history)

        # Simulate ContextWindowExceededError and truncation
        controller.state.history = controller._apply_conversation_window(
            controller.state.history
        )

        # Verify truncation occurred
        assert len(controller.state.history) < original_history_len
        assert controller.state.start_id == first_msg._id
        assert controller.state.truncation_id is not None
        assert controller.state.truncation_id > controller.state.start_id

    def test_truncation_state_persistence_with_real_stores(self, mock_agent):
        """
        Test that truncation state is properly saved and restored across sessions using real in-memory stores.

        This test verifies the complete lifecycle of truncation:
        1. Creating a session with many events
        2. Forcing truncation
        3. Saving state to persistent storage
        4. Restoring state in a new session
        5. Verifying all IDs and events are preserved correctly
        6. Adding more events and forcing truncation again
        7. Verifying the system maintains correct state across multiple truncations

        The test uses real in-memory stores instead of mocks to ensure the actual behavior
        is tested end-to-end.
        """
        # Use an in-memory file store for state persistence
        from openhands.storage.memory import InMemoryFileStore

        file_store = InMemoryFileStore()

        # Use a real event stream with in-memory storage
        from openhands.events import EventStream

        # Create a real event stream with the in-memory file store
        event_stream = EventStream(sid='test_persistence', file_store=file_store)

        # PHASE 1: Create initial session with events

        # Create first user message and add it to the event stream
        first_msg = MessageAction(content='Start task', wait_for_response=False)
        event_stream.add_event(first_msg, EventSource.USER)
        first_msg_id = first_msg.id

        # Create a large number of events (100 pairs of commands and observations)
        events = [first_msg]
        for i in range(100):
            cmd = CmdRunAction(command=f'cmd{i}')
            event_stream.add_event(cmd, EventSource.AGENT)

            obs = CmdOutputObservation(
                command=f'cmd{i}', content=f'output{i}', command_id=cmd.id
            )
            event_stream.add_event(obs, EventSource.ENVIRONMENT)

            events.extend([cmd, obs])

        total_events_count = len(events)

        # Create the first controller with all events in the stream
        controller1 = AgentController(
            agent=mock_agent,
            event_stream=event_stream,
            max_iterations=10,
            sid='test_persistence',
            confirmation_mode=False,
            headless_mode=True,
        )

        # Verify initial state before truncation
        assert controller1.state.start_id == first_msg_id
        # The truncation_id might be initialized to -1 in the State class, so check for that
        assert (
            controller1.state.truncation_id == -1
            or controller1.state.truncation_id is None
        )
        assert len(controller1.state.history) == total_events_count

        # PHASE 2: Force truncation and verify immediate effects

        # Force truncation
        controller1._handle_long_context_error()

        # Calculate expected truncation ID based on the algorithm in _apply_conversation_window
        # The midpoint index is approximately len(events) // 2
        # For 201 events (1 initial + 100 pairs), midpoint is around 100
        # Since the truncation algorithm preserves action-observation pairs,
        # the truncation_id should be set to the ID of an event near the midpoint
        expected_truncation_id = 100  # This is the ID of the event at the midpoint

        # Verify truncation occurred with correct truncation_id
        assert controller1.state.truncation_id is not None
        assert controller1.state.truncation_id == expected_truncation_id

        # Verify start_id is still preserved after truncation
        assert controller1.state.start_id == first_msg_id

        # Verify history was cut approximately in half
        truncated_history_len = len(controller1.state.history)
        assert truncated_history_len < total_events_count
        assert (
            truncated_history_len >= total_events_count * 0.4
        )  # Should be roughly half
        assert (
            truncated_history_len <= total_events_count * 0.6
        )  # Allow some flexibility

        # Verify first message is still in history after truncation
        assert first_msg in controller1.state.history

        # Verify all events in truncated history are either the first message or after truncation_id
        for event in controller1.state.history:
            if event.id != first_msg_id:
                assert event.id >= controller1.state.truncation_id

        # PHASE 3: Save state and create a new session

        # Save state to persistent storage
        controller1.state.save_to_session('test_persistence', file_store)

        # Store values for comparison after restoration
        truncation_id = controller1.state.truncation_id
        start_id = controller1.state.start_id

        # Close the first controller
        asyncio.run(controller1.close())

        # PHASE 4: Create new controller and restore state

        # Create a new controller with the same event stream and session ID
        controller2 = AgentController(
            agent=mock_agent,
            event_stream=event_stream,
            max_iterations=10,
            sid='test_persistence',
            confirmation_mode=False,
            headless_mode=True,
        )

        # Restore state from persistent storage
        from openhands.controller.state.state import State

        controller2.state = State.restore_from_session('test_persistence', file_store)

        # Verify state was restored correctly before initializing history
        assert controller2.state.truncation_id == truncation_id
        assert controller2.state.start_id == start_id

        # Initialize history from the event stream
        controller2._init_history()

        # PHASE 5: Verify restored state and history

        # Verify IDs are still preserved after _init_history
        assert controller2.state.truncation_id == truncation_id
        assert controller2.state.start_id == start_id

        # Calculate expected minimum length: events from truncation_id onwards + first message
        events_from_truncation_id = [e for e in events if e.id >= truncation_id]
        expected_min_length = 1 + len(events_from_truncation_id)  # 1 for first_msg

        # Verify the history was loaded correctly
        assert len(controller2.state.history) >= expected_min_length
        assert first_msg in controller2.state.history

        # Verify the truncated history contains the right events
        for event in controller2.state.history:
            if event.id != first_msg_id:  # Skip first message which is always included
                assert (
                    event.id >= controller2.state.truncation_id
                ), f'Event {event.id} is before truncation_id {controller2.state.truncation_id}'

        # PHASE 6: Add more events and force another truncation

        # Add 50 more pairs of events
        for i in range(100, 150):
            cmd = CmdRunAction(command=f'cmd{i}')
            event_stream.add_event(cmd, EventSource.AGENT)

            obs = CmdOutputObservation(
                command=f'cmd{i}', content=f'output{i}', command_id=cmd.id
            )
            event_stream.add_event(obs, EventSource.ENVIRONMENT)

            # Add to controller's history directly to simulate normal operation
            controller2.state.history.extend([cmd, obs])

        # Store history length before second truncation
        history_len_before_second_truncation = len(controller2.state.history)

        # Force another truncation
        controller2._handle_long_context_error()

        # Verify second truncation occurred
        assert len(controller2.state.history) < history_len_before_second_truncation

        # Verify start_id is still preserved after second truncation
        assert controller2.state.start_id == first_msg_id

        # Verify truncation_id has been updated to a higher value
        assert controller2.state.truncation_id > truncation_id

        # Verify first message is still in history after second truncation
        assert first_msg in controller2.state.history

        # PHASE 7: Save state again and create a third session

        # Save state after second truncation
        controller2.state.save_to_session('test_persistence', file_store)

        # Store values for comparison after second restoration
        second_truncation_id = controller2.state.truncation_id

        # Close the second controller
        asyncio.run(controller2.close())

        # Create a third controller
        controller3 = AgentController(
            agent=mock_agent,
            event_stream=event_stream,
            max_iterations=10,
            sid='test_persistence',
            confirmation_mode=False,
            headless_mode=True,
        )

        # Restore state from persistent storage
        controller3.state = State.restore_from_session('test_persistence', file_store)

        # Verify state was restored correctly before initializing history
        assert controller3.state.truncation_id == second_truncation_id
        assert controller3.state.start_id == first_msg_id

        # Initialize history from the event stream
        controller3._init_history()

        # PHASE 8: Verify final state after multiple truncations

        # Verify IDs are still preserved after multiple truncations
        assert controller3.state.truncation_id == second_truncation_id
        assert controller3.state.start_id == first_msg_id

        # Verify first message is still in history
        assert first_msg in controller3.state.history

        # Verify all events in final history are either the first message or after second truncation_id
        for event in controller3.state.history:
            if event.id != first_msg_id:
                assert event.id >= controller3.state.truncation_id

        # Clean up resources
        asyncio.run(controller3.close())
        event_stream.close()

        # Note: There may still be a RuntimeWarning about 'coroutine AgentController._on_event was never awaited'
        # This is expected and doesn't affect the test results. The warning occurs because the event handling
        # in AgentController.on_event uses asyncio.get_event_loop().run_until_complete() which can leave
        # some coroutines unresolved when the test ends.
