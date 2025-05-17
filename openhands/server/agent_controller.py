"""Agent controller module for the server."""

from typing import Optional

from openhands.controller.agent_controller import AgentController
from openhands.server.shared import conversation_manager

_agent_controller: Optional[AgentController] = None


def get_agent_controller() -> Optional[AgentController]:
    """Get the global agent controller instance.

    Returns:
        Optional[AgentController]: The global agent controller instance, or None if not available.
    """
    global _agent_controller

    # If we already have an agent controller, return it
    if _agent_controller is not None:
        return _agent_controller

    # Try to get the agent controller from the active conversation
    active_conversation = conversation_manager.get_active_conversation()
    if active_conversation and hasattr(active_conversation, 'controller'):
        _agent_controller = active_conversation.controller
        return _agent_controller

    return None
