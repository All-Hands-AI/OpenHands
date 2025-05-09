from enum import Enum


class ConversationStatus(Enum):
    RUNNING = 'RUNNING'
    STOPPED = 'STOPPED'
    ERROR = 'ERROR'
