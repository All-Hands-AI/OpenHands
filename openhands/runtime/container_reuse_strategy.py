from enum import Enum


class ContainerReuseStrategy(Enum):
    """Strategy for reusing containers between runtime sessions."""

    NONE = 'none'
    PAUSE = 'pause'
    KEEP_ALIVE = 'keep_alive'
