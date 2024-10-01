from abc import abstractmethod
import asyncio
from dataclasses import dataclass, field
from typing import Dict
from uuid import UUID

from fastapi import WebSocket
from pydantic import TypeAdapter
from oh.event.oh_event import OhEvent
from oh.fastapi.websocket_conversation_listener import WebsocketConversationListener
from oh.conversation.conversation_abc import ConversationABC
from oh.conversation_broker.conversation_broker_listener_abc import ConversationBrokerListenerABC


@dataclass
class WebsocketConversationBrokerListener(ConversationBrokerListenerABC):
    websocket: WebSocket
    event_info_adapter: TypeAdapter
    listeners: Dict[UUID, WebsocketConversationListener] = field(default_factory=dict)

    @abstractmethod
    async def after_create_conversation(self, conversation: ConversationABC):
        listener = WebsocketConversationListener(conversation.id, self.websocket, self.event_info_adapter)
        id = await conversation.add_listener(listener)
        self.listeners[id] = listener

    @abstractmethod
    async def before_destroy_conversation(self, conversation: ConversationABC):
        tasks = []
        for listener_id, conversation_listener in self.listeners.items():
            if conversation_listener.conversation_id == conversation.id:
                tasks.append(asyncio.create_task(conversation.remove_listener(listener_id)))
        await asyncio.wait(tasks)
