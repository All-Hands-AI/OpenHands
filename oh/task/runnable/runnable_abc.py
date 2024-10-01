from __future__ import annotations
from abc import ABC, abstractmethod
from uuid import UUID

from oh.conversation import conversation_abc
from oh.task import runnable_progress_listener_abc


class RunnableABC(ABC):
    """
    Some runnable task. Runnables should endeavour to be good asyncio neighbors and not lock up
    the main run loop too much. They may also implement cancellability by checking that the
    status of the task is not CANCELLING in the service.
    """

    cancellable: bool = False

    @abstractmethod
    async def run(
        self,
        task_id: UUID,
        progress_listener: runnable_progress_listener_abc.RunnableProgressListenerABC,
        conversation: conversation_abc.ConversationABC,
    ):
        """
        Execute this task
        task_id: The id of this task
        progress_listener: Used to alert external actors of changes in progress
        conversation: Conversation in which this task is run
        """
