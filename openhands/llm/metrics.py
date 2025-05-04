import copy
import time

from pydantic import BaseModel, Field


class Cost(BaseModel):
    model: str
    cost: float
    timestamp: float = Field(default_factory=time.time)


class ResponseLatency(BaseModel):
    """Metric tracking the round-trip time per completion call."""

    model: str
    latency: float
    response_id: str


class TokenUsage(BaseModel):
    """Metric tracking detailed token usage per completion call."""

    model: str = Field(default='')
    prompt_tokens: int = Field(default=0)
    completion_tokens: int = Field(default=0)
    cache_read_tokens: int = Field(default=0)
    cache_write_tokens: int = Field(default=0)
    response_id: str = Field(default='')

    def __add__(self, other: 'TokenUsage') -> 'TokenUsage':
        """Add two TokenUsage instances together."""
        return TokenUsage(
            model=self.model,
            prompt_tokens=self.prompt_tokens + other.prompt_tokens,
            completion_tokens=self.completion_tokens + other.completion_tokens,
            cache_read_tokens=self.cache_read_tokens + other.cache_read_tokens,
            cache_write_tokens=self.cache_write_tokens + other.cache_write_tokens,
            response_id=self.response_id,
        )


class Metrics:
    """Metrics class can record various metrics during running and evaluation.
    We track:
      - accumulated_cost and costs
      - A list of ResponseLatency
      - A list of TokenUsage (one per call).
    """

    def __init__(self, model_name: str = 'default') -> None:
        self._accumulated_cost: float = 0.0
        self._costs: list[Cost] = []
        self._response_latencies: list[ResponseLatency] = []
        self.model_name = model_name
        self._token_usages: list[TokenUsage] = []
        self._accumulated_token_usage: TokenUsage = TokenUsage(
            model=model_name,
            prompt_tokens=0,
            completion_tokens=0,
            cache_read_tokens=0,
            cache_write_tokens=0,
            response_id='',
        )

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

    @property
    def response_latencies(self) -> list[ResponseLatency]:
        if not hasattr(self, '_response_latencies'):
            self._response_latencies = []
        return self._response_latencies

    @response_latencies.setter
    def response_latencies(self, value: list[ResponseLatency]) -> None:
        self._response_latencies = value

    @property
    def token_usages(self) -> list[TokenUsage]:
        if not hasattr(self, '_token_usages'):
            self._token_usages = []
        return self._token_usages

    @token_usages.setter
    def token_usages(self, value: list[TokenUsage]) -> None:
        self._token_usages = value

    @property
    def accumulated_token_usage(self) -> TokenUsage:
        """Get the accumulated token usage, initializing it if it doesn't exist."""
        if not hasattr(self, '_accumulated_token_usage'):
            self._accumulated_token_usage = TokenUsage(
                model=self.model_name,
                prompt_tokens=0,
                completion_tokens=0,
                cache_read_tokens=0,
                cache_write_tokens=0,
                response_id='',
            )
        return self._accumulated_token_usage

    def add_cost(self, value: float) -> None:
        if value < 0:
            raise ValueError('Added cost cannot be negative.')
        self._accumulated_cost += value
        self._costs.append(Cost(cost=value, model=self.model_name))

    def add_response_latency(self, value: float, response_id: str) -> None:
        self._response_latencies.append(
            ResponseLatency(
                latency=max(0.0, value), model=self.model_name, response_id=response_id
            )
        )

    def add_token_usage(
        self,
        prompt_tokens: int,
        completion_tokens: int,
        cache_read_tokens: int,
        cache_write_tokens: int,
        response_id: str,
    ) -> None:
        """Add a single usage record."""
        usage = TokenUsage(
            model=self.model_name,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cache_read_tokens=cache_read_tokens,
            cache_write_tokens=cache_write_tokens,
            response_id=response_id,
        )
        self._token_usages.append(usage)

        # Update accumulated token usage using the __add__ operator
        self._accumulated_token_usage = self.accumulated_token_usage + TokenUsage(
            model=self.model_name,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cache_read_tokens=cache_read_tokens,
            cache_write_tokens=cache_write_tokens,
            response_id='',
        )

    def merge(self, other: 'Metrics') -> None:
        """Merge 'other' metrics into this one."""
        self._accumulated_cost += other.accumulated_cost
        self._costs += other._costs
        # use the property so older picked objects that lack the field won't crash
        self.token_usages += other.token_usages
        self.response_latencies += other.response_latencies

        # Merge accumulated token usage using the __add__ operator
        self._accumulated_token_usage = (
            self.accumulated_token_usage + other.accumulated_token_usage
        )

    def get(self) -> dict:
        """Return the metrics in a dictionary."""
        return {
            'accumulated_cost': self._accumulated_cost,
            'accumulated_token_usage': self.accumulated_token_usage.model_dump(),
            'costs': [cost.model_dump() for cost in self._costs],
            'response_latencies': [
                latency.model_dump() for latency in self._response_latencies
            ],
            'token_usages': [usage.model_dump() for usage in self._token_usages],
        }

    def reset(self) -> None:
        self._accumulated_cost = 0.0
        self._costs = []
        self._response_latencies = []
        self._token_usages = []
        # Reset accumulated token usage with a new instance
        self._accumulated_token_usage = TokenUsage(
            model=self.model_name,
            prompt_tokens=0,
            completion_tokens=0,
            cache_read_tokens=0,
            cache_write_tokens=0,
            response_id='',
        )

    def log(self) -> str:
        """Log the metrics."""
        metrics = self.get()
        logs = ''
        for key, value in metrics.items():
            logs += f'{key}: {value}\n'
        return logs

    def copy(self) -> 'Metrics':
        """Create a deep copy of the Metrics object."""
        return copy.deepcopy(self)

    def __repr__(self) -> str:
        return f'Metrics({self.get()}'
