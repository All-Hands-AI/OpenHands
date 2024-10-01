from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from oh.task.task_status import TaskStatus
from oh.task.runnable import runnable_abc


@dataclass
class OhTask:
    conversation_id: UUID
    runnable: runnable_abc.RunnableABC
    id: UUID = field(default_factory=uuid4)
    status: TaskStatus = TaskStatus.PENDING
    title: Optional[str] = None
    code: Optional[str] = None
    progress: Optional[float] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
