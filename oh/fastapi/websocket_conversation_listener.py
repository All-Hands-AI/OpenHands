from dataclasses import dataclass
from uuid import UUID

from fastapi import WebSocket
from pydantic import TypeAdapter
from oh.event.oh_event import OhEvent
from oh.fastapi.task_update import TaskUpdate
from oh.conversation.listener.conversation_listener_abc import ConversationListenerABC
from oh.task.oh_task import OhTask


@dataclass
class WebsocketConversationListener(ConversationListenerABC):
    conversation_id: UUID
    websocket: WebSocket
    event_info_adapter: TypeAdapter

    async def on_event(self, event: OhEvent):
        if self.conversation_id != event.conversation_id:
            return
        data = self.event_info_adapter.dump_json(event).decode("UTF-8")
        await self.websocket.send_text(data)
