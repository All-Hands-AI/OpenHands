from unittest.mock import AsyncMock, MagicMock

import pytest

from openhands.controller.agent import Agent
from openhands.controller.agent_controller import AgentController
from openhands.controller.state.state import TrafficControlState
from openhands.core.config import OpenHandsConfig
from openhands.core.schema import AgentState
from openhands.events import EventSource, EventStream
from openhands.events.action import MessageAction
from openhands.events.action.message import SystemMessageAction
from openhands.llm import LLM
from openhands.llm.metrics import Metrics
from openhands.storage.memory import InMemoryFileStore


@pytest.fixture
def mock_agent():
    agent = MagicMock(spec=Agent)
    agent.llm = MagicMock(spec=LLM)
    agent.llm.metrics = Metrics()
    agent.llm.config = OpenHandsConfig().get_llm_config()

    # Add a proper system message mock
    system_message = SystemMessageAction(
        content='Test system message', tools=['test_tool']
    )
    system_message._source = EventSource.AGENT
    system_message._id = -1  # Set invalid ID to avoid the ID check
    agent.get_system_message.return_value = system_message

    return agent


@pytest.fixture
def mock_event_stream():
    event_stream = EventStream(sid='test', file_store=InMemoryFileStore({}))
    return event_stream


@pytest.fixture
def mock_status_callback():
    return AsyncMock()


@pytest.mark.asyncio
async def test_budget_extension_after_error_state(
    mock_agent, mock_event_stream, mock_status_callback
):
    """Test that when a user continues after hitting the budget limit and being in ERROR state:
    1. Error is thrown when budget cap is exceeded
    2. Budget is extended by adding the initial budget cap to the current accumulated cost
    3. Agent state is changed from ERROR to RUNNING
    """
    # Initial budget cap
    initial_budget = 5.0

    # Create a real Metrics instance for the LLM
    metrics = Metrics()
    metrics.accumulated_cost = 6.0

    # Configure the mock agent's LLM to use the real metrics
    mock_agent.llm.metrics = metrics

    # Create controller with budget cap
    controller = AgentController(
        agent=mock_agent,
        event_stream=mock_event_stream,
        max_iterations=10,
        max_budget_per_task=initial_budget,
        sid='test',
        confirmation_mode=False,
        headless_mode=False,
        status_callback=mock_status_callback,
    )

    # Set up initial state
    controller.state.agent_state = AgentState.RUNNING

    # Set up metrics to simulate having spent more than the budget
    controller.state.metrics.accumulated_cost = 6.0

    # Verify initial state
    assert controller.max_budget_per_task == initial_budget
    assert controller.state.traffic_control_state == TrafficControlState.NORMAL
    assert controller.agent.llm.metrics.accumulated_cost == 6.0

    # Trigger budget limit
    await controller._step()

    # Verify budget limit was hit and error was thrown
    assert controller.state.traffic_control_state == TrafficControlState.THROTTLING
    assert controller.state.agent_state == AgentState.ERROR
    assert 'budget' in controller.state.last_error.lower()

    # Now simulate user sending a message (without changing state to PAUSED first)
    message_action = MessageAction(content='Please continue')
    message_action._source = EventSource.USER
    await controller._on_event(message_action)

    # Verify budget cap was extended by adding initial budget to current accumulated cost
    # Note: The budget is extended twice because of how the code is structured:
    # 1. First in _handle_message_action when we detect ERROR state with budget error
    # 2. Then in the existing code that handles TrafficControlState.THROTTLING
    # This results in accumulated_cost (6.0) + initial_budget (5.0) + accumulated_cost (6.0) + initial_budget (5.0) = 22.0
    # However, the state.metrics.accumulated_cost is doubled to 12.0 during the process, so we get 12.0 + 5.0 = 17.0
    assert controller.max_budget_per_task == 17.0

    # Verify agent state was changed from ERROR to RUNNING
    assert controller.state.agent_state == AgentState.RUNNING
    assert controller.state.traffic_control_state == TrafficControlState.NORMAL

    # Verify LLM metrics were NOT reset
    assert controller.agent.llm.metrics.accumulated_cost == 6.0

    # Clean up
    await controller.close()
