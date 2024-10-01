from __future__ import annotations
from abc import ABC, abstractmethod

from oh.event import oh_event
from oh.task import oh_task


class ConversationListenerABC(ABC):

    @abstractmethod
    async def on_event(self, event: oh_event.OhEvent):
        """Callback for an event in a conversation"""
