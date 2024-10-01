import asyncio
from dataclasses import dataclass
from typing import Dict, Optional
from uuid import UUID

from oh.event.detail.task_status_update import TaskStatusUpdate
from oh.conversation.listener.conversation_listener_abc import ConversationListenerABC
from oh.conversation.conversation_abc import ConversationABC
from oh.storage.storage_abc import StorageABC
from oh.task.oh_task import OhTask
from oh.task.runnable_progress_listener_abc import RunnableProgressListenerABC
from oh.task.task_filter import TaskFilter
from oh.task.task_status import TaskStatus


@dataclass
class AsyncioProgressListener(RunnableProgressListenerABC):
    task_id: UUID
    storage: StorageABC[OhTask, TaskFilter]
    conversation: ConversationABC

    async def update_progress(
        self, task_id: UUID, code: Optional[str], progress: Optional[float]
    ):
        task = await self.storage.read(task_id)
        if task.status != TaskStatus.RUNNING:
            return
        task.code = code
        task.progress = progress
        await self.storage.update(task)
        await self.conversation.trigger_event(
            TaskStatusUpdate(
                task_id=task.id,
                status=task.status,
                code=task.code,
                progress=task.progress,
            )
        )
