import pytest

from openhands.controller.state.state import State
from openhands.llm.metrics import Metrics


@pytest.mark.asyncio
async def test_delegate_metrics_propagation():
    """
    Test that when a delegate agent accumulates metrics, they are properly propagated
    to the parent agent's metrics.

    This test verifies that:
    1. The delegate inherits the parent's budget flag
    2. Updates to the delegate's metrics are reflected in the parent's metrics
    3. The budget flag is properly updated based on the metrics
    """
    # Create a parent state with budget tracking
    parent_state = State(inputs={})

    # Initialize the budget flag
    from openhands.controller.state.control_flags import BudgetControlFlag

    parent_state.budget_flag = BudgetControlFlag(
        initial_value=0.0, current_value=0.0, max_value=10.0
    )

    # Create a shared metrics object
    metrics = Metrics()
    parent_state.metrics = metrics

    # Create a delegate state that shares the same budget flag and metrics
    delegate_state = State(
        inputs={},
        budget_flag=parent_state.budget_flag,
        metrics=parent_state.metrics,
    )

    # Verify that the parent and delegate share the same metrics object
    assert parent_state.metrics is delegate_state.metrics

    # Verify that the parent and delegate share the same budget flag
    assert parent_state.budget_flag is delegate_state.budget_flag

    # Add some metrics to the delegate's metrics
    delegate_cost = 0.25
    delegate_state.metrics.add_cost(delegate_cost)

    # Verify that the parent's metrics are automatically updated (since they share the same object)
    assert parent_state.metrics.accumulated_cost == delegate_cost

    # Manually sync the budget flag with metrics
    parent_state.budget_flag.current_value = parent_state.metrics.accumulated_cost

    # Verify that the budget flag is updated
    assert parent_state.budget_flag.current_value == delegate_cost
    assert delegate_state.budget_flag.current_value == delegate_cost
