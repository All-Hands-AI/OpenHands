from typing import Callable

from prometheus_client import Gauge, make_asgi_app
from server.clustered_conversation_manager import ClusteredConversationManager

from openhands.server.shared import (
    conversation_manager,
)

RUNNING_AGENT_LOOPS_GAUGE = Gauge(
    'saas_running_agent_loops',
    'Count of running agent loops, aggregate by session_id to dedupe',
    ['session_id'],
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
    metrics_callable = make_asgi_app()

    async def wrapped_handler(scope, receive, send):
        """
        Call _update_metrics before serving Prometheus metrics endpoint.
        Not wrapped in a `try`, failing would make metrics endpoint unavailable.
        """
        await _update_metrics()
        await metrics_callable(scope, receive, send)

    return wrapped_handler
