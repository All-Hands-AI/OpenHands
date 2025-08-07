from enum import Enum


class ConversationStatus(Enum):
    Warning = 'WARNING'
    RUNNING = 'RUNNING'
    FINISHED = 'FINISHED'
    ERROR = 'ERROR'
    STOPPED = 'STOPPED'
