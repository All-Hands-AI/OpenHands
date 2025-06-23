"""
Conversation-level metrics management for thread-safe LLM cost tracking.

This module provides a conversation-scoped metrics manager that ensures
all LLM objects within a conversation share the same metrics instance
and accumulate costs in a thread-safe manner.
"""

import queue
import threading
from typing import Any, Optional

from openhands.llm.metrics import Cost, Metrics, ResponseLatency, TokenUsage


class MetricsOperation:
    """Base class for metrics operations that can be queued."""

    def apply(self, metrics: Metrics) -> None:
        """Apply this operation to the metrics object."""
        raise NotImplementedError


class AddCostOperation(MetricsOperation):
    """Operation to add cost to metrics."""

    def __init__(self, value: float):
        self.value = value

    def apply(self, metrics: Metrics) -> None:
        metrics.add_cost(self.value)


class AddResponseLatencyOperation(MetricsOperation):
    """Operation to add response latency to metrics."""

    def __init__(self, value: float, response_id: str):
        self.value = value
        self.response_id = response_id

    def apply(self, metrics: Metrics) -> None:
        metrics.add_response_latency(self.value, self.response_id)


class AddTokenUsageOperation(MetricsOperation):
    """Operation to add token usage to metrics."""

    def __init__(
        self,
        prompt_tokens: int,
        completion_tokens: int,
        cache_read_tokens: int,
        cache_write_tokens: int,
        context_window: int,
        response_id: str,
    ):
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens
        self.cache_read_tokens = cache_read_tokens
        self.cache_write_tokens = cache_write_tokens
        self.context_window = context_window
        self.response_id = response_id

    def apply(self, metrics: Metrics) -> None:
        metrics.add_token_usage(
            self.prompt_tokens,
            self.completion_tokens,
            self.cache_read_tokens,
            self.cache_write_tokens,
            self.context_window,
            self.response_id,
        )


class ConversationMetrics:
    """
    Thread-safe metrics manager for a conversation.

    This class manages a single Metrics instance per conversation and provides
    thread-safe operations for multiple LLM objects to accumulate costs.
    Uses a queue-based approach to handle concurrent access.
    """

    def __init__(self, model_name: str = 'conversation'):
        self._metrics = Metrics(model_name=model_name)
        self._operation_queue: queue.Queue[MetricsOperation] = queue.Queue()
        self._lock = threading.Lock()
        self._processing = False

    def _process_queue(self) -> None:
        """Process all pending operations in the queue."""
        with self._lock:
            if self._processing:
                return
            self._processing = True

        try:
            while True:
                try:
                    operation = self._operation_queue.get_nowait()
                    operation.apply(self._metrics)
                    self._operation_queue.task_done()
                except queue.Empty:
                    break
        finally:
            with self._lock:
                self._processing = False

    def add_cost(self, value: float) -> None:
        """Thread-safe method to add cost."""
        self._operation_queue.put(AddCostOperation(value))
        self._process_queue()

    def add_response_latency(self, value: float, response_id: str) -> None:
        """Thread-safe method to add response latency."""
        self._operation_queue.put(AddResponseLatencyOperation(value, response_id))
        self._process_queue()

    def add_token_usage(
        self,
        prompt_tokens: int,
        completion_tokens: int,
        cache_read_tokens: int,
        cache_write_tokens: int,
        context_window: int,
        response_id: str,
    ) -> None:
        """Thread-safe method to add token usage."""
        self._operation_queue.put(
            AddTokenUsageOperation(
                prompt_tokens,
                completion_tokens,
                cache_read_tokens,
                cache_write_tokens,
                context_window,
                response_id,
            )
        )
        self._process_queue()

    @property
    def accumulated_cost(self) -> float:
        """Get the current accumulated cost."""
        self._process_queue()
        return self._metrics.accumulated_cost

    @property
    def max_budget_per_task(self) -> Optional[float]:
        """Get the max budget per task."""
        return self._metrics.max_budget_per_task

    @max_budget_per_task.setter
    def max_budget_per_task(self, value: Optional[float]) -> None:
        """Set the max budget per task."""
        self._metrics.max_budget_per_task = value

    @property
    def costs(self) -> list[Cost]:
        """Get the list of costs."""
        self._process_queue()
        return self._metrics.costs

    @property
    def response_latencies(self) -> list[ResponseLatency]:
        """Get the list of response latencies."""
        self._process_queue()
        return self._metrics.response_latencies

    @property
    def token_usages(self) -> list[TokenUsage]:
        """Get the list of token usages."""
        self._process_queue()
        return self._metrics.token_usages

    @property
    def accumulated_token_usage(self) -> TokenUsage:
        """Get the accumulated token usage."""
        self._process_queue()
        return self._metrics.accumulated_token_usage

    def get_metrics(self) -> Metrics:
        """Get the underlying metrics object (after processing queue)."""
        self._process_queue()
        return self._metrics

    def get(self) -> dict[str, Any]:
        """Return the metrics in a dictionary."""
        self._process_queue()
        return self._metrics.get()

    def log(self) -> str:
        """Log the metrics."""
        self._process_queue()
        return self._metrics.log()

    def copy(self) -> Metrics:
        """Create a deep copy of the underlying Metrics object."""
        self._process_queue()
        return self._metrics.copy()

    def diff(self, baseline: Metrics) -> Metrics:
        """Calculate the difference between current metrics and a baseline."""
        self._process_queue()
        return self._metrics.diff(baseline)

    def merge(self, other: Metrics) -> None:
        """Merge other metrics into this one."""
        # For thread safety, we'll add individual operations rather than direct merge
        for cost in other.costs:
            self.add_cost(cost.cost)

        for latency in other.response_latencies:
            self.add_response_latency(latency.latency, latency.response_id)

        for usage in other.token_usages:
            self.add_token_usage(
                usage.prompt_tokens,
                usage.completion_tokens,
                usage.cache_read_tokens,
                usage.cache_write_tokens,
                usage.context_window,
                usage.response_id,
            )


class ThreadSafeMetrics(Metrics):
    """
    A thread-safe wrapper around the Metrics class.

    This class provides the same interface as Metrics but delegates
    operations to a ConversationMetrics instance for thread safety.
    """

    def __init__(
        self, conversation_metrics: ConversationMetrics, model_name: str = 'default'
    ):
        # Don't call super().__init__ to avoid creating duplicate state
        self._conversation_metrics = conversation_metrics
        self.model_name = model_name

    @property
    def accumulated_cost(self) -> float:
        return self._conversation_metrics.accumulated_cost

    @accumulated_cost.setter
    def accumulated_cost(self, value: float) -> None:
        # For setting, we need to calculate the difference and add it
        current = self._conversation_metrics.accumulated_cost
        if value > current:
            self._conversation_metrics.add_cost(value - current)
        elif value < current:
            raise ValueError('Cannot decrease accumulated cost')

    @property
    def max_budget_per_task(self) -> Optional[float]:
        return self._conversation_metrics.max_budget_per_task

    @max_budget_per_task.setter
    def max_budget_per_task(self, value: Optional[float]) -> None:
        self._conversation_metrics.max_budget_per_task = value

    @property
    def costs(self) -> list[Cost]:
        return self._conversation_metrics.costs

    @property
    def response_latencies(self) -> list[ResponseLatency]:
        return self._conversation_metrics.response_latencies

    @response_latencies.setter
    def response_latencies(self, value: list[ResponseLatency]) -> None:
        # This setter is used in some places, but for thread safety,
        # we'll just log a warning and not implement it
        import warnings

        warnings.warn(
            'Setting response_latencies directly is not supported in ThreadSafeMetrics. '
            'Use add_response_latency instead.',
            UserWarning,
            stacklevel=2,
        )

    @property
    def token_usages(self) -> list[TokenUsage]:
        return self._conversation_metrics.token_usages

    @token_usages.setter
    def token_usages(self, value: list[TokenUsage]) -> None:
        # This setter is used in some places, but for thread safety,
        # we'll just log a warning and not implement it
        import warnings

        warnings.warn(
            'Setting token_usages directly is not supported in ThreadSafeMetrics. '
            'Use add_token_usage instead.',
            UserWarning,
            stacklevel=2,
        )

    @property
    def accumulated_token_usage(self) -> TokenUsage:
        return self._conversation_metrics.accumulated_token_usage

    def add_cost(self, value: float) -> None:
        self._conversation_metrics.add_cost(value)

    def add_response_latency(self, value: float, response_id: str) -> None:
        self._conversation_metrics.add_response_latency(value, response_id)

    def add_token_usage(
        self,
        prompt_tokens: int,
        completion_tokens: int,
        cache_read_tokens: int,
        cache_write_tokens: int,
        context_window: int,
        response_id: str,
    ) -> None:
        self._conversation_metrics.add_token_usage(
            prompt_tokens,
            completion_tokens,
            cache_read_tokens,
            cache_write_tokens,
            context_window,
            response_id,
        )

    def merge(self, other: Metrics) -> None:
        self._conversation_metrics.merge(other)

    def get(self) -> dict[str, Any]:
        return self._conversation_metrics.get()

    def log(self) -> str:
        return self._conversation_metrics.log()

    def copy(self) -> Metrics:
        return self._conversation_metrics.copy()

    def diff(self, baseline: Metrics) -> Metrics:
        return self._conversation_metrics.diff(baseline)

    def __repr__(self) -> str:
        return f'ThreadSafeMetrics({self._conversation_metrics.get()})'
