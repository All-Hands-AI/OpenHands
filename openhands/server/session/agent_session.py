"""Deprecated shim: AgentSession moved to openhands.session.agent_session.

This module exists for backward compatibility. New code should import:
    from openhands.session.agent_session import AgentSession
"""

from openhands.session.agent_session import (  # noqa: F401
    WAIT_TIME_BEFORE_CLOSE,
    WAIT_TIME_BEFORE_CLOSE_INTERVAL,
    AgentSession,
)

__all__ = [
    'AgentSession',
    'WAIT_TIME_BEFORE_CLOSE',
    'WAIT_TIME_BEFORE_CLOSE_INTERVAL',
]
