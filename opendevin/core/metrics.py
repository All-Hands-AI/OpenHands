class Metrics:
    """
    Metrics class can record various metrics during running and evaluation.
    Currently we define the following metrics:
        total_cost: the total cost of the current LLM.
    """

    def __init__(self) -> None:
        self._total_cost: float = 0.0
        self._costs: list[float] = []
        self.reset()

    @property
    def total_cost(self) -> float:
        return self._total_cost

    @total_cost.setter
    def total_cost(self, value: float) -> None:
        if value < 0:
            raise ValueError('Total cost cannot be negative.')
        self._total_cost = value

    @property
    def costs(self) -> list:
        return self._costs

    def add_cost(self, value: float) -> None:
        if value < 0:
            raise ValueError('Added cost cannot be negative.')
        self._total_cost += value
        self._costs.append(value)

    def reset(self):
        """
        Reset all metrics to zero value.
        """
        self._total_cost = 0
        self._costs = []

    def get(self):
        """
        Return the metrics in a dictionary.
        """
        return {'total_cost': self._total_cost, 'costs': self._costs}

    def log(self):
        """
        Log the metrics.
        """
        metrics = self.get()
        logs = ''
        for key, value in metrics.items():
            logs += f'{key}: {value}\n'
        return logs
