import asyncio
from dataclasses import dataclass
from datetime import datetime
from typing import Literal
from uuid import UUID
from oh.conversation.conversation_abc import ConversationABC
from oh.task.runnable.runnable_abc import RunnableABC
from oh.task.runnable_progress_listener_abc import RunnableProgressListenerABC
from oh.task.task_status import TaskStatus


@dataclass
class Ticker(RunnableABC):
    """
    Runnable that sends message events at regular intervals
    (Mostly for debugging purposes)
    """

    type: Literal["Ticker"] = "Ticker"
    cancellable: bool = True
    message: str = "The time is now {time}"
    interval: int = 1
    iterations: int = 100

    async def run(
        self,
        task_id: UUID,
        progress_listener: RunnableProgressListenerABC,
        conversation: ConversationABC,
    ):
        iteration = 0
        while (
            await conversation.get_task(task_id)
        ).status == TaskStatus.RUNNING and iteration < self.iterations:
            await progress_listener.update_progress(
                task_id, "processing", float(iteration) / self.iterations
            )
            iteration += 1
            await asyncio.sleep(self.interval)
