import asyncio
from dataclasses import dataclass
from datetime import datetime
from typing import Literal
from uuid import UUID
from oh.conversation.conversation_abc import ConversationABC
from oh.event.detail.text_reply import TextReply
from oh.task.runnable.runnable_abc import RunnableABC
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
        conversation: ConversationABC,
    ):
        iteration = 0
        while (
            await conversation.get_task(task_id)
        ).status == TaskStatus.RUNNING and iteration < self.iterations:
            conversation.trigger_event(TextReply(self.message.format(time=str(datetime.now()))))
            iteration += 1
            await asyncio.sleep(self.interval)
