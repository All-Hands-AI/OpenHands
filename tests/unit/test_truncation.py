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

    # Create a step function that returns an action without an ID
    def agent_step_fn(state):
        return MessageAction(content='Agent returned a message')

    agent.step = agent_step_fn

    return agent


class TestTruncation:
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
