

import asyncio
from dataclasses import dataclass
from typing import Literal
from uuid import UUID
from oh.conversation.conversation_abc import ConversationABC
from oh.task.runnable.runnable_abc import RunnableABC


@dataclass
class Wait(RunnableABC):
    type: Literal["Wait"] = "Wait"
    cancellable: bool = False
    timeout: int = 5

    async def run(self, task_id: UUID, conversation: ConversationABC):
        asyncio.sleep(self.timeout)
