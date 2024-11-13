from unittest.mock import MagicMock, patch

import pytest
from litellm.exceptions import ContextWindowExceededError

from openhands.controller.agent_controller import AgentController
from openhands.events import EventSource, EventStream
from openhands.events.action import CmdRunAction, MessageAction
from openhands.events.observation import CmdOutputObservation
from openhands.storage import get_file_store


@pytest.fixture
def temp_dir(tmp_path_factory: pytest.TempPathFactory) -> str:
    return str(tmp_path_factory.mktemp('test_truncation'))


@pytest.fixture
def event_stream(temp_dir):
    file_store = get_file_store('local', temp_dir)
    event_stream = EventStream('test_truncation', file_store)
    yield event_stream
    event_stream.clear()


@pytest.fixture
def mock_agent():
    return MagicMock()


class TestTruncation:
    def test_apply_conversation_window_basic(self, event_stream, mock_agent):
        controller = AgentController(
            agent=mock_agent,
            event_stream=event_stream,
            max_iterations=10,
            sid='test_truncation',
            confirmation_mode=False,
            headless_mode=True,
        )

        # Create a sequence of events
        first_msg = MessageAction(content='Hello, start task', wait_for_response=False)
        first_msg._source = EventSource.USER
        first_msg._id = 1

        cmd1 = CmdRunAction(command='ls')
        cmd1._id = 2
        obs1 = CmdOutputObservation(command='ls', content='file1.txt', command_id=2)
        obs1._cause = cmd1._id

        cmd2 = CmdRunAction(command='pwd')
        cmd2._id = 3
        obs2 = CmdOutputObservation(command='pwd', content='/home', command_id=3)
        obs2._cause = cmd2._id

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

    @pytest.mark.asyncio
    async def test_context_window_exceeded_handling(self, event_stream, mock_agent):
        controller = AgentController(
            agent=mock_agent,
            event_stream=event_stream,
            max_iterations=10,
            sid='test_truncation',
            confirmation_mode=False,
            headless_mode=True,
        )

        # Setup initial history
        first_msg = MessageAction(content='Start task', wait_for_response=False)
        first_msg._source = EventSource.USER
        first_msg._id = 1
        event_stream.add_event(first_msg, EventSource.USER)

        cmd1 = CmdRunAction(command='ls')
        cmd1._id = 2
        event_stream.add_event(cmd1, EventSource.AGENT)

        obs1 = CmdOutputObservation(command='ls', content='file1.txt', command_id=2)
        obs1._cause = cmd1._id
        event_stream.add_event(obs1, EventSource.ENVIRONMENT)

        # Initialize controller history
        await controller._init_history()
        original_history_len = len(controller.state.history)

        # Simulate ContextWindowExceededError
        with patch.object(mock_agent, 'step', side_effect=ContextWindowExceededError()):
            await controller._step()

        # Verify truncation occurred
        assert len(controller.state.history) < original_history_len
        assert controller.state.start_id == first_msg._id
        assert controller.state.truncation_id is not None
        assert controller.state.truncation_id > controller.state.start_id

    @pytest.mark.asyncio
    async def test_history_restoration_after_truncation(self, event_stream, mock_agent):
        controller = AgentController(
            agent=mock_agent,
            event_stream=event_stream,
            max_iterations=10,
            sid='test_truncation',
            confirmation_mode=False,
            headless_mode=True,
        )

        # Add events to stream
        first_msg = MessageAction(content='Start task', wait_for_response=False)
        first_msg._source = EventSource.USER
        first_msg._id = 1
        event_stream.add_event(first_msg, EventSource.USER)

        for i in range(5):
            cmd = CmdRunAction(command=f'cmd{i}')
            cmd._id = i + 2
            event_stream.add_event(cmd, EventSource.AGENT)

            obs = CmdOutputObservation(
                command=f'cmd{i}', content=f'output{i}', command_id=cmd._id
            )
            obs._cause = cmd._id
            event_stream.add_event(obs, EventSource.ENVIRONMENT)

        # Initialize and force truncation
        await controller._init_history()
        original_history = controller.state.history.copy()

        # Simulate truncation
        truncated = controller._apply_conversation_window(original_history)
        controller.state.history = truncated

        # Save truncation state
        saved_start_id = controller.state.start_id
        saved_truncation_id = controller.state.truncation_id

        # Create new controller instance
        new_controller = AgentController(
            agent=mock_agent,
            event_stream=event_stream,
            max_iterations=10,
            sid='test_truncation',
            confirmation_mode=False,
            headless_mode=True,
        )
        new_controller.state.start_id = saved_start_id
        new_controller.state.truncation_id = saved_truncation_id

        # Initialize history with saved IDs
        await new_controller._init_history()

        # Verify restoration
        assert len(new_controller.state.history) == len(truncated)
        assert new_controller.state.history[0] == first_msg
        assert new_controller.state.start_id == saved_start_id
        assert all(
            isinstance(e, (MessageAction, CmdRunAction, CmdOutputObservation))
            for e in new_controller.state.history
        )
