from enum import Enum


class ConversationStatus(Enum):
    STARTING = 'STARTING'
    RUNNING = 'RUNNING'
    STOPPED = 'STOPPED'
