from dataclasses import dataclass
from typing import Literal, Optional
from uuid import UUID

from oh.event.detail.event_detail_abc import EventDetailABC
from oh.conversation.conversation_status import ConversationStatus
from oh.task.task_status import TaskStatus


@dataclass
class TaskStatusUpdate(EventDetailABC):
    """Event indicating that the status of a task has changed"""
    task_id: UUID
    status: TaskStatus
    code: Optional[str] = None
    progress: Optional[float] = None
    type: Literal["TaskStatusUpdate"] = "TaskStatusUpdate"
