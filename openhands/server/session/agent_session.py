"""Deprecated shim: AgentSession moved to openhands.session.agent_session.

This module exists for backward compatibility. New code should import:
    from openhands.session.agent_session import AgentSession
"""

# For legacy tests that patch these via this shim's module path
from openhands.controller import AgentController  # noqa: F401
from openhands.events.stream import EventStream  # noqa: F401
from openhands.memory.memory import Memory  # noqa: F401
from openhands.session.agent_session import (  # noqa: F401
    WAIT_TIME_BEFORE_CLOSE,
    WAIT_TIME_BEFORE_CLOSE_INTERVAL,
    AgentSession,
)

__all__ = [
    'AgentSession',
    'WAIT_TIME_BEFORE_CLOSE',
    'WAIT_TIME_BEFORE_CLOSE_INTERVAL',
    'AgentController',
    'EventStream',
    'Memory',
]
