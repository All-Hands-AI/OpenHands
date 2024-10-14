import time

from pydantic import BaseModel, Field


class Cost(BaseModel):
    model: str
    cost: float
    timestamp: float = Field(default_factory=time.time)


class Metrics:
    """Metrics class can record various metrics during running and evaluation.
    Currently, we define the following metrics:
        accumulated_cost: the total cost (USD $) of the current LLM.
    """

    def __init__(self, model_name: str = 'default') -> None:
        self._accumulated_cost: float = 0.0
        self._costs: list[Cost] = []
        self.model_name = model_name

    @property
    def accumulated_cost(self) -> float:
        return self._accumulated_cost

    @accumulated_cost.setter
    def accumulated_cost(self, value: float) -> None:
        if value < 0:
            raise ValueError('Total cost cannot be negative.')
        self._accumulated_cost = value

    @property
    def costs(self) -> list[Cost]:
        return self._costs

    def add_cost(self, value: float) -> None:
        if value < 0:
            raise ValueError('Added cost cannot be negative.')
        self._accumulated_cost += value
        self._costs.append(Cost(cost=value, model=self.model_name))

    def merge(self, other: 'Metrics') -> None:
        self._accumulated_cost += other.accumulated_cost
        self._costs += other._costs

    def get(self) -> dict:
        """Return the metrics in a dictionary."""
        return {
            'accumulated_cost': self._accumulated_cost,
            'costs': [cost.model_dump() for cost in self._costs],
        }

    def reset(self):
        self._accumulated_cost = 0.0
        self._costs = []

    def log(self):
        """Log the metrics."""
        metrics = self.get()
        logs = ''
        for key, value in metrics.items():
            logs += f'{key}: {value}\n'
        return logs

    def __repr__(self):
        return f'Metrics({self.get()}'
