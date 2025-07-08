from enum import Enum


class ExitReason(Enum):
    INTENTIONAL = 'intentional'
    INTERRUPTED = 'interrupted'
    ERROR = 'error'
