import pytest

from openhands.controller.agent_controller import (
    AgentController,
    AgentState,
    TrafficControlState,
)


@pytest.mark.asyncio
async def test_budget_increase_via_set_agent_state(mock_agent, mock_event_stream):
    # Set up controller with a conversation budget cap
    controller = AgentController(
        agent=mock_agent,
        event_stream=mock_event_stream,
        max_iterations=10,
        max_budget_per_task=20,
        max_budget_per_conversation=10,
        sid='test',
        confirmation_mode=False,
        headless_mode=False,
    )
    controller.state.agent_state = AgentState.PAUSED
    controller.state.traffic_control_state = TrafficControlState.THROTTLING
    controller.state.metrics.accumulated_cost = 10.1

    # Original budget caps
    original_task_budget = controller.max_budget_per_task
    original_conversation_budget = controller.max_budget_per_conversation

    # Simulate user clicking "Resume" button
    await controller.set_agent_state_to(AgentState.RUNNING)

    # Check that both budget caps were increased by adding the initial budget
    assert (
        controller.max_budget_per_task
        == original_task_budget + controller._initial_max_budget_per_task
    )
    assert (
        controller.max_budget_per_conversation
        == original_conversation_budget
        + controller._initial_max_budget_per_conversation
    )

    await controller.close()
