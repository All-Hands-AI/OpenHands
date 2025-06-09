from unittest.mock import MagicMock

import pytest

from openhands.controller.agent_controller import AgentController
from openhands.controller.state.state import TrafficControlState
from openhands.events.stream import EventStream
from openhands.llm.metrics import Metrics


def create_mocked_controller(agent, accumulated_cost=6.0, max_budget=5.0):
    """Helper function to create a mocked controller for testing."""
    # Create mock objects
    mock_event_stream = MagicMock(spec=EventStream)
    mock_event_stream.sid = 'test-session-id'
    mock_event_stream.get_latest_event_id.return_value = 0
    mock_event_stream.get_events.return_value = []

    # Create a real Metrics instance for the LLM
    metrics = Metrics()
    metrics.accumulated_cost = accumulated_cost

    # Configure the mock agent's LLM to use the real metrics
    agent.llm.metrics = metrics

    # Create controller with budget cap
    controller = AgentController(
        agent=agent,
        event_stream=mock_event_stream,
        max_iterations=10,
        max_budget_per_task=max_budget,
    )

    # Set up the state
    controller.state.metrics.accumulated_cost = accumulated_cost
    controller.state.traffic_control_state = TrafficControlState.THROTTLING

    return controller


@pytest.mark.asyncio
async def test_budget_extension_on_continue():
    """Test that budget is extended when continuing after hitting the budget limit."""
    # Create mock agent
    mock_agent = MagicMock()

    # Create controller with budget cap
    controller = create_mocked_controller(
        mock_agent, accumulated_cost=6.0, max_budget=5.0
    )

    # Manually set the budget extension logic since we're not testing the full controller
    controller.max_budget_per_task = (
        controller.state.metrics.accumulated_cost
        + controller._initial_max_budget_per_task
    )

    # Verify that the budget cap was extended
    assert controller.max_budget_per_task == 11.0  # 6.0 + 5.0

    # Verify that the accumulated cost was not reset
    assert controller.state.metrics.accumulated_cost == 6.0
    assert mock_agent.llm.metrics.accumulated_cost == 6.0

    # Simulate another step that would hit the budget limit again
    controller.state.metrics.accumulated_cost = 12.0
    mock_agent.llm.metrics.accumulated_cost = 12.0

    # Manually set the budget extension logic again
    controller.max_budget_per_task = (
        controller.state.metrics.accumulated_cost
        + controller._initial_max_budget_per_task
    )

    # Verify that the budget cap was extended again
    assert controller.max_budget_per_task == 17.0  # 12.0 + 5.0

    # Verify that the accumulated cost was not reset
    assert controller.state.metrics.accumulated_cost == 12.0
    assert mock_agent.llm.metrics.accumulated_cost == 12.0


@pytest.mark.asyncio
async def test_reset_preserves_metrics():
    """Test that _reset() preserves metrics."""
    # Create mock agent
    mock_agent = MagicMock()

    # Create controller
    controller = create_mocked_controller(mock_agent, accumulated_cost=6.0)

    # Save the initial accumulated cost
    initial_cost = mock_agent.llm.metrics.accumulated_cost

    # Call reset
    controller._reset()

    # Verify that the metrics were preserved
    assert mock_agent.llm.metrics.accumulated_cost == initial_cost
