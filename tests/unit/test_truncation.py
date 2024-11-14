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

    def test_history_restoration_after_truncation(self, mock_event_stream, mock_agent):
        controller = AgentController(
            agent=mock_agent,
            event_stream=mock_event_stream,
            max_iterations=10,
            sid='test_truncation',
            confirmation_mode=False,
            headless_mode=True,
        )

        # Create events with IDs
        first_msg = MessageAction(content='Start task', wait_for_response=False)
        first_msg._source = EventSource.USER
        first_msg._id = 1

        events = [first_msg]
        for i in range(5):
            cmd = CmdRunAction(command=f'cmd{i}')
            cmd._id = i + 2
            obs = CmdOutputObservation(
                command=f'cmd{i}', content=f'output{i}', command_id=cmd._id
            )
            obs._cause = cmd._id
            events.extend([cmd, obs])

        # Set up initial history
        controller.state.history = events.copy()

        # Force truncation
        controller.state.history = controller._apply_conversation_window(
            controller.state.history
        )

        # Save state
        saved_start_id = controller.state.start_id
        saved_truncation_id = controller.state.truncation_id
        saved_history_len = len(controller.state.history)

        # Set up mock event stream for new controller
        mock_event_stream.get_events.return_value = controller.state.history

        # Create new controller with saved state
        new_controller = AgentController(
            agent=mock_agent,
            event_stream=mock_event_stream,
            max_iterations=10,
            sid='test_truncation',
            confirmation_mode=False,
            headless_mode=True,
        )
        new_controller.state.start_id = saved_start_id
        new_controller.state.truncation_id = saved_truncation_id
        new_controller.state.history = mock_event_stream.get_events()

        # Verify restoration
        assert len(new_controller.state.history) == saved_history_len
        assert new_controller.state.history[0] == first_msg
        assert new_controller.state.start_id == saved_start_id
