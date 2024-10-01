from enum import Enum


class TaskStatus(Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    CANCELLING = "CANCELLING"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"
    ERROR = "ERROR"


FINISHED_STATUSES = (TaskStatus.CANCELLED, TaskStatus.COMPLETED, TaskStatus.ERROR)
