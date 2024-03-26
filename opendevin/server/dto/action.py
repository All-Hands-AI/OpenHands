from enum import Enum


class EventAction(str, Enum):
    """Event Actions"""

    INIT = "initialize"
    """Initialize the agent and controller.
    """

    CHAT = "chat"

    START = "start"
    """Start a task.
    """

