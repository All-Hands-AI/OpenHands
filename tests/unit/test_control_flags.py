import pytest

from openhands.controller.state.control_flags import (
    BudgetControlFlag,
    IterationControlFlag,
)


def test_iteration_control_flag_reaches_limit_and_increases():
    flag = IterationControlFlag(limit_increase_amount=5, current_value=5, max_value=5)

    # Should be at limit
    assert flag.reached_limit() is True
    assert flag._hit_limit is True

    # Increase limit in non-headless mode
    flag.increase_limit(headless_mode=False)
    assert flag.max_value == 10  # increased by limit_increase_amount

    # After increase, we should no longer be at limit
    flag._hit_limit = False  # simulate reset
    assert flag.reached_limit() is False


def test_iteration_control_flag_does_not_increase_in_headless():
    flag = IterationControlFlag(limit_increase_amount=5, current_value=5, max_value=5)

    assert flag.reached_limit() is True
    assert flag._hit_limit is True

    # Should NOT increase max_value in headless mode
    flag.increase_limit(headless_mode=True)
    assert flag.max_value == 5


def test_iteration_control_flag_step_behavior():
    flag = IterationControlFlag(limit_increase_amount=2, current_value=0, max_value=2)

    # First step
    flag.step()
    assert flag.current_value == 1
    assert not flag.reached_limit()

    # Second step
    flag.step()
    assert flag.current_value == 2
    assert flag.reached_limit()

    # Stepping again should raise error
    with pytest.raises(RuntimeError, match='Agent reached maximum iteration'):
        flag.step()


# ----- BudgetControlFlag Tests -----


def test_budget_control_flag_reaches_limit_and_increases():
    flag = BudgetControlFlag(
        limit_increase_amount=10.0, current_value=50.0, max_value=50.0
    )

    # Should be at limit
    assert flag.reached_limit() is True
    assert flag._hit_limit is True

    # Increase budget — allowed only if _hit_limit == True
    flag.increase_limit(headless_mode=False)
    assert flag.max_value == 60.0  # current_value + limit_increase_amount

    # After increasing, _hit_limit should be reset manually in your logic
    flag._hit_limit = False
    flag.current_value = 55.0
    assert flag.reached_limit() is False


def test_budget_control_flag_does_not_increase_if_not_hit_limit():
    flag = BudgetControlFlag(
        limit_increase_amount=10.0, current_value=40.0, max_value=50.0
    )

    # Not at limit yet
    assert flag.reached_limit() is False
    assert flag._hit_limit is False

    # Try to increase — should do nothing
    old_max_value = flag.max_value
    flag.increase_limit(headless_mode=False)
    assert flag.max_value == old_max_value


def test_budget_control_flag_does_not_increase_in_headless():
    flag = BudgetControlFlag(
        limit_increase_amount=10.0, current_value=50.0, max_value=50.0
    )

    assert flag.reached_limit() is True
    assert flag._hit_limit is True

    # Increase limit in headless mode — should still increase since BudgetControlFlag ignores headless param
    flag.increase_limit(headless_mode=True)
    assert flag.max_value == 60.0


def test_budget_control_flag_step_raises_on_limit():
    flag = BudgetControlFlag(
        limit_increase_amount=5.0, current_value=55.0, max_value=50.0
    )

    # Should raise RuntimeError
    with pytest.raises(RuntimeError, match='Agent reached maximum budget'):
        flag.step()

    # After increasing limit, step should not raise
    flag.max_value = 60.0
    flag._hit_limit = False
    flag.step()  # Should not raise


def test_budget_control_flag_hit_limit_resets_after_increase():
    flag = BudgetControlFlag(
        limit_increase_amount=10.0, current_value=50.0, max_value=50.0
    )

    # Initially should hit limit
    assert flag.reached_limit() is True
    assert flag._hit_limit is True

    # Increase limit
    flag.increase_limit(headless_mode=False)

    # After increasing, _hit_limit should be reset
    assert flag._hit_limit is False

    # Should no longer report reaching limit unless value exceeds new max
    assert flag.reached_limit() is False

    # If we push current_value over new max_value:
    flag.current_value = flag.max_value + 1.0
    assert flag.reached_limit() is True
