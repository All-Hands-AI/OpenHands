import logging
import os
from typing import Callable

from prometheus_client import CollectorRegistry, Gauge, generate_latest
from server.clustered_conversation_manager import ClusteredConversationManager

import openhands.server.shared

logger = logging.getLogger(__name__)

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
    if isinstance(
        openhands.server.shared.conversation_manager, ClusteredConversationManager
    ):
        running_agent_loops = await openhands.server.shared.conversation_manager.get_running_agent_loops_locally()
        # In multiprocess mode, do NOT call clear() as it can delete memory-mapped files
        if not os.environ.get('PROMETHEUS_MULTIPROC_DIR'):
            RUNNING_AGENT_LOOPS_GAUGE.clear()
        # running_agent_loops shouldn't be None, but can be.
        if running_agent_loops is not None:
            for sid in running_agent_loops:
                RUNNING_AGENT_LOOPS_GAUGE.labels(session_id=sid).set(1)


def metrics_app() -> Callable:
    """
    Create metrics ASGI app with multiprocess support.

    When PROMETHEUS_MULTIPROC_DIR is set, uses MultiProcessCollector to aggregate
    metrics across all uvicorn worker processes.
    """

    async def wrapped_handler(scope, receive, send):
        try:
            await _update_metrics()
        except Exception as e:
            logger.error(f'Failed to update metrics: {e}', exc_info=True)

        if 'PROMETHEUS_MULTIPROC_DIR' in os.environ:
            from prometheus_client import multiprocess

            registry = CollectorRegistry()
            multiprocess.MultiProcessCollector(registry)
            metrics_data = generate_latest(registry)
        else:
            from prometheus_client import REGISTRY

            metrics_data = generate_latest(REGISTRY)

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
