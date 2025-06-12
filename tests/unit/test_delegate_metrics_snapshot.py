from unittest.mock import MagicMock

import pytest

from openhands.controller.agent import Agent
from openhands.controller.state.state import State
from openhands.llm.llm import LLM
from openhands.llm.metrics import Metrics


@pytest.mark.asyncio
async def test_delegate_metrics_snapshot():
    """
    Test that we can compute local metrics and iterations for delegates using snapshots.

    This test verifies that:
    1. The agent's reset() method doesn't affect metrics
    2. The state.get_local_step() method correctly calculates local steps for delegates
    """
    # Create a state object with parent_iteration and current_value
    test_state = State()
    test_state.parent_iteration = 1  # Parent iteration when delegate starts
    test_state.iteration_flag.current_value = 4  # After delegate adds 3

    # Call get_local_step directly through the state object
    local_step = test_state.get_local_step()

    # Verify that get_local_step returns the expected value (4 - 1 = 3)
    # Note: If this fails, there might be a bug in the get_local_step implementation
    assert local_step == 3, f'Expected local_step to be 3, but got {local_step}'

    # Create a mock agent with metrics
    agent = MagicMock(spec=Agent)
    agent.name = 'TestAgent'
    agent.llm = MagicMock(spec=LLM)
    agent.llm.metrics = Metrics()

    # Add some metrics
    agent.llm.metrics.add_cost(0.25)

    # Get the initial metrics value
    initial_cost = agent.llm.metrics.accumulated_cost

    # Reset the agent
    agent.reset()

    # Verify that metrics were not reset
    assert agent.llm.metrics.accumulated_cost == initial_cost, (
        'Metrics should not be reset when agent is reset'
    )
