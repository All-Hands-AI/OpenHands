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



    def test_truncation_state_persistence_with_real_stores(
        self, mock_agent
    ):
        """Test that truncation state is properly saved and restored across sessions using real in-memory stores."""
        # Use an in-memory file store for state persistence
        from openhands.storage.memory import InMemoryFileStore
        file_store = InMemoryFileStore()
        
        # Use a real event stream with in-memory storage
        from openhands.events import EventStream
        
        # Create a real event stream with the in-memory file store
        event_stream = EventStream(sid='test_persistence', file_store=file_store)
        
        # First session: Create controller and events
        controller1 = AgentController(
            agent=mock_agent,
            event_stream=event_stream,
            max_iterations=10,
            sid='test_persistence',
            confirmation_mode=False,
            headless_mode=True,
        )

        # Create events with IDs and add them to the event stream
        first_msg = MessageAction(content='Start task', wait_for_response=False)
        event_stream.add_event(first_msg, EventSource.USER)
        
        # Create a large number of events (100 pairs)
        events = [first_msg]
        for i in range(100):
            cmd = CmdRunAction(command=f'cmd{i}')
            event_stream.add_event(cmd, EventSource.AGENT)
            
            obs = CmdOutputObservation(
                command=f'cmd{i}', content=f'output{i}', command_id=cmd.id
            )
            event_stream.add_event(obs, EventSource.ENVIRONMENT)
            
            events.extend([cmd, obs])

        # Set up initial history
        controller1.state.history = events.copy()

        # Force truncation
        controller1._handle_long_context_error()

        # Verify truncation occurred
        assert controller1.state.truncation_id > 0

        # Verify history was cut approximately in half (as per _apply_conversation_window implementation)
        # It might not be exactly half due to action-observation pair preservation
        expected_approx_length = max(1, len(events) // 2) + 1  # +1 for first message if not in second half
        assert len(controller1.state.history) <= len(events) * 0.6  # Should be roughly half, with some buffer
        assert len(controller1.state.history) >= expected_approx_length * 0.8  # Allow some flexibility

        truncated_history_len = len(controller1.state.history)
        truncation_id = controller1.state.truncation_id

        # Save state to persistent storage
        controller1.state.save_to_session('test_persistence', file_store)

        # Close the first controller to clean up resources
        asyncio.run(controller1.close())
        
        # Create a new event stream for the second controller
        event_stream2 = EventStream(sid='test_persistence', file_store=file_store)
        
        # Second session: Create new controller and restore state
        controller2 = AgentController(
            agent=mock_agent,
            event_stream=event_stream2,
            max_iterations=10,
            sid='test_persistence_2',
            confirmation_mode=False,
            headless_mode=True,
        )

        # Restore state
        from openhands.controller.state.state import State
        controller2.state = State.restore_from_session(
            'test_persistence', file_store
        )

        # Verify state was restored
        assert controller2.state.truncation_id == truncation_id
        assert controller2.state.start_id == controller1.state.start_id

        # Load history using the controller's method
        controller2._init_history()

        # Verify history was loaded correctly
        # The restored history should contain:
        # 1. The first user message
        # 2. All events from truncation_id onwards
        
        # Calculate expected minimum length: events from truncation_id onwards + first message
        events_from_truncation_id = [e for e in events if e.id >= truncation_id]
        expected_min_length = 1 + len(events_from_truncation_id)  # 1 for first_msg
        
        assert len(controller2.state.history) >= expected_min_length
        assert first_msg in controller2.state.history

        # Verify the truncated history contains the right events
        for event in controller2.state.history:
            if event.id != first_msg.id:  # Skip first message which is always included
                assert (
                    event.id >= controller2.state.truncation_id
                ), f'Event {event.id} is before truncation_id {controller2.state.truncation_id}'


