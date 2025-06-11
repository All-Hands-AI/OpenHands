from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Generic, TypeVar

T = TypeVar(
    'T', int, float
)  # Type for the value (int for iterations, float for budget)



@dataclass
class ControlFlag(Generic[T]):
    """Base class for control flags that manage limits and state transitions."""

    initial_value: T
    current_value: T
    max_value: T
    headless_mode: bool = False
    _hit_limit: bool = False

    def reached_limit(self) -> bool:
        """Check if the limit has been reached.

        Returns:
            bool: True if the limit has been reached, False otherwise.
        """
        raise NotImplementedError

    def expand(self, headless_mode: bool) -> None:
        """Expand the limit when needed."""
        raise NotImplementedError


    def next(self):
        """Determine the next state based on the current state and mode.

        Returns:
            ControlFlagState: The next state.
        """
        raise NotImplementedError

    def update(self, value: T) -> None:
        """Update the current value.

        Args:
            value: The new value.
        """
        self.current_value = value


@dataclass
class IterationControlFlag(ControlFlag[int]):
    """Control flag for managing iteration limits."""

    def reached_limit(self) -> bool:
        """Check if the iteration limit has been reached."""
        self._hit_limit = self.current_value >= self.max_value
        return self._hit_limit

    def expand(self, headless_mode: bool) -> None:
        """Expand the iteration limit by adding the initial value."""
        if not headless_mode and self._hit_limit:
            self.max_value += self.initial_value

    def next(self):
        # Increment the current value
        self.current_value += 1

        if self.reached_limit():
            raise RuntimeError(
                f'Agent reached maximum iteration. '
                f'Current iteration: {self.current_value}, max iteration: {self.max_value}'
            )





@dataclass
class BudgetControlFlag(ControlFlag[float]):
    """Control flag for managing budget limits."""

    def reached_limit(self) -> bool:
        """Check if the budget limit has been reached."""
        self._hit_limit = self.current_value > self.max_value
        return self._hit_limit

    def expand(self, headless_mode) -> None:
        """Expand the budget limit by adding the initial value to the current value."""
        if self._hit_limit:
            self.max_value = self.current_value + self.initial_value

    def next(self):
        """Check if we've reached the limit and update state accordingly.

        Note: Unlike IterationControlFlag, this doesn't increment the value
        as the budget is updated externally.
        """
        if self.reached_limit():
            raise RuntimeError(
                f'Agent reached maximum budget for conversation.'
                f'Current budget: {self.current_value}, max budget: {self.max_value}'
            )



