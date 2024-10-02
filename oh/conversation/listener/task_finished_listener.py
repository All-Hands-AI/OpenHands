from asyncio import Condition, Future
from dataclasses import field
from typing import Dict, List, Set
from uuid import UUID
from oh.conversation.listener.conversation_listener_abc import ConversationListenerABC
from oh.event.detail.task_status_update import TaskStatusUpdate
from oh.event.oh_event import OhEvent
from oh.task.task_status import TaskStatus


class TaskFinishedListener(ConversationListenerABC):
    """
    Listener that allows waiting for tasks to finish before proceeding
    """

    finished: Dict[UUID, Condition] = field(default_factory=dict)

    async def on_event(self, event: OhEvent):
        detail = event.detail
        if isinstance(detail, TaskStatusUpdate) and detail.status in [
            TaskStatus.CANCELLED,
            TaskStatus.ERROR,
            TaskStatus.COMPLETED,
        ]:
            condition = self._get_condition(detail.task_id)
            async with condition:
                condition.notify()

    async def on_task_finished(self, task_id: UUID):
        condition = self._get_condition(task_id)
        await condition.wait()

    def _get_condition(self, task_id: UUID):
        condition = self.finished.get(task_id)
        if not condition:
            condition = self.finished[task_id] = Condition()
        return condition
