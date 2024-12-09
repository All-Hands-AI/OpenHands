import asyncio
import pytest
from unittest.mock import MagicMock

from openhands.controller.agent_controller import AgentController
from openhands.controller.agent import Agent
from openhands.controller.state.state import State
from openhands.core.schema.agent import AgentState
from openhands.events.stream import EventStream
from openhands.events.action import MessageAction
from openhands.events.event import EventSource
from openhands.events.observation.error import ErrorObservation


@pytest.mark.asyncio
async def test_stuck_recovery():
    # Mock dependencies
    event_stream = EventStream("test_session", MagicMock())
    agent = MagicMock(spec=Agent)
    agent.name = "test_agent"
    agent.sandbox_plugins = []

    # Mock LLM
    llm_mock = MagicMock()
    llm_mock.metrics = {}
    llm_mock.config.model = "test_model"
    llm_mock.config.base_url = "test_url"
    llm_mock.config.draft_editor = None
    agent.llm = llm_mock

    # Create controller
    controller = AgentController(
        sid="test_session",
        event_stream=event_stream,
        agent=agent,
        max_iterations=10,
        confirmation_mode=False,
        headless_mode=True,
    )

    # Add repeated messages to simulate stuck state
    message = MessageAction("test message", wait_for_response=False)
    observation = ErrorObservation("test error", "test_cause")

    # Add 4 pairs of the same message and observation to simulate a loop
    for _ in range(4):
        controller.state.history.append(message)
        controller.state.history.append(observation)

    # Verify stuck detection
    assert controller._stuck_detector.is_stuck()

    # Simulate error handling
    await controller._react_to_exception(RuntimeError("Agent got stuck in a loop"))

    # Verify state is reset
    assert len(controller.state.history) == 0
    assert controller.state.agent_state == AgentState.ERROR

    # Create a message and set its source directly
    new_message = MessageAction("new message", wait_for_response=False)
    new_message._source = EventSource.USER  # Access private attribute for testing

    # Verify controller can process new messages
    await controller._handle_message_action(new_message)
    assert controller.state.agent_state == AgentState.RUNNING
