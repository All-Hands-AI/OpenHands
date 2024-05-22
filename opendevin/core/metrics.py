class Metrics:
    """
    Metrics class can record various metrics during running and evaluation.
    Currently we define the following metrics:
        accumulated_cost: the total cost (USD $) of the current LLM.
    """

    def __init__(self) -> None:
        self._accumulated_cost: float = 0.0
        self._costs: list[float] = []

    @property
    def accumulated_cost(self) -> float:
        return self._accumulated_cost

    @accumulated_cost.setter
    def accumulated_cost(self, value: float) -> None:
        if value < 0:
            raise ValueError('Total cost cannot be negative.')
        self._accumulated_cost = value

    @property
    def costs(self) -> list:
        return self._costs

    def add_cost(self, value: float) -> None:
        if value < 0:
            raise ValueError('Added cost cannot be negative.')
        self._accumulated_cost += value
        self._costs.append(value)

    def get(self):
        """
        Return the metrics in a dictionary.
        """
        return {'accumulated_cost': self._accumulated_cost, 'costs': self._costs}

    def log(self):
        """
        Log the metrics.
        """
        metrics = self.get()
        logs = ''
        for key, value in metrics.items():
            logs += f'{key}: {value}\n'
        return logs
