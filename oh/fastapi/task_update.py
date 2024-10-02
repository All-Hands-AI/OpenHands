from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel

from oh.task.task_status import TaskStatus


class TaskUpdate(BaseModel):
    id: UUID
    status: TaskStatus
    type: Literal["TaskUpdate"] = "TaskUpdate"
