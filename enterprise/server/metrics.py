import os
from typing import Callable

from prometheus_client import CollectorRegistry, Gauge, generate_latest
from server.clustered_conversation_manager import ClusteredConversationManager

from openhands.server.shared import (
    conversation_manager,
)

# Use livesum mode for multiprocess support - this aggregates gauge values
# across all worker processes, counting only living processes
RUNNING_AGENT_LOOPS_GAUGE = Gauge(
    'saas_running_agent_loops',
    'Count of running agent loops, aggregate by session_id to dedupe',
    ['session_id'],
    multiprocess_mode='livesum',
)


async def _update_metrics():
    """Update any prometheus metrics that are not updated during normal operation."""
    if isinstance(conversation_manager, ClusteredConversationManager):
        running_agent_loops = (
            await conversation_manager.get_running_agent_loops_locally()
        )
        # Clear so we don't keep counting old sessions.
        # This is theoretically a race condition but this is scraped on a regular interval.
        RUNNING_AGENT_LOOPS_GAUGE.clear()
        # running_agent_loops shouldn't be None, but can be.
        if running_agent_loops is not None:
            for sid in running_agent_loops:
                RUNNING_AGENT_LOOPS_GAUGE.labels(session_id=sid).set(1)


def metrics_app() -> Callable:
    """
    Create metrics ASGI app with multiprocess support.

    When PROMETHEUS_MULTIPROC_DIR is set, uses MultiProcessCollector to aggregate
    metrics across all uvicorn worker processes. This prevents duplicate/conflicting
    metrics when the same time series is exported by different workers.
    """

    async def wrapped_handler(scope, receive, send):
        """
        Call _update_metrics before serving Prometheus metrics endpoint.
        Not wrapped in a `try`, failing would make metrics endpoint unavailable.
        """
        await _update_metrics()

        # Check if multiprocess mode is enabled
        if 'PROMETHEUS_MULTIPROC_DIR' in os.environ:
            # In multiprocess mode, create a new registry and collect from all workers
            from prometheus_client import multiprocess

            registry = CollectorRegistry()
            multiprocess.MultiProcessCollector(registry)
            metrics_data = generate_latest(registry)
        else:
            # Single process mode - use default registry
            from prometheus_client import REGISTRY

            metrics_data = generate_latest(REGISTRY)

        # Send HTTP response with metrics
        await send(
            {
                'type': 'http.response.start',
                'status': 200,
                'headers': [
                    [b'content-type', b'text/plain; version=0.0.4; charset=utf-8'],
                ],
            }
        )
        await send(
            {
                'type': 'http.response.body',
                'body': metrics_data,
            }
        )

    return wrapped_handler
