from enum import Enum


class ResearchMode(str, Enum):
    CHAT = 'chat'
    """Chat mode.
    """

    DEEP_RESEARCH = 'deep_research'
    """Deep research mode.
    """

    FOLLOW_UP = 'follow_up'
    """Follow up mode.
    """
