from enum import Enum


class ConversationStatus(Enum):
    STARTING = 'STARTING'
    RUNNING = 'RUNNING'
    STOPPING = 'STOPPING'
    STOPPED = 'STOPPED'
