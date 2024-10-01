

from dataclasses import dataclass, field
from itertools import count
from typing import Dict, Optional
from uuid import UUID, uuid4

from httpx import URL
import httpx
from pydantic import TypeAdapter
from oh.fastapi.conversation_info import ConversationInfo
from oh.conversation.conversation_abc import ConversationABC
from oh.conversation.conversation_filter import ConversationFilter
from oh.conversation_broker.conversation_broker_abc import ConversationBrokerABC
from oh.conversation_broker.conversation_broker_listener_abc import ConversationBrokerListenerABC
from oh.storage.page import Page

_SESSION_INFO_PAGE_ADAPTER = TypeAdapter(Page[ConversationInfo])



@dataclass
class RemoteConversationBroker(ConversationBrokerABC):
    """
    Manages conversations in a remote server.
    NOTE: Does not fire after_create_conversation and before_destroy_conversation if the operation did not go through this server.
    Is that reasonable? Do we need a different channel for events for these? I think we may...

    Maybe we need a global event list that actually includes conversation ids?
    """

    root_url: URL
    listeners: Dict[UUID, ConversationBrokerListenerABC] = field(default_factory=dict)
    httpx_client: httpx.AsyncClient = None

    def __post_init__(self):
        self.httpx_client = httpx.AsyncClient()

    async def add_listener(self, listener: ConversationBrokerListenerABC) -> UUID:
        # We need a websocket here...
        listener_id = uuid4()
        self.listeners[listener_id] = listener
        return listener_id

    async def remove_listener(self, listener_id: UUID) -> bool:
        return self.listeners.pop(listener_id) is not None

    async def get_conversation(self, conversation_id: UUID) -> Optional[ConversationABC]:
        response = await self.httpx_client.get(f"{self.root_url}conversation/{conversation_id}")
        response_json = response.json
        if response_json:
            conversation_info = ConversationInfo.model_validate(response_json)
            return RemoteConversation(conversation_info)

    async def search_conversations(
        self, filter: Optional[ConversationFilter] = None, page_id: Optional[str] = None
    ) -> Page[ConversationABC]:
        response = await self.httpx_client.get(f"{self.root_url}conversation/")
        page = _SESSION_INFO_PAGE_ADAPTER.model_validate(response.json)
        return page

    async def count_conversations(self, filter: Optional[ConversationFilter]) -> int:
        response = await self.httpx_client.get(f"{self.root_url}conversation-count/")
        return response.json

    async def create_conversation(
        self,
    ) -> ConversationABC:
        response = await self.httpx_client.post(f"{self.root_url}conversation/")
        conversation_info = ConversationInfo.model_validate(response.json)
        conversation = RemoteConversation(conversation_info)
        for listener in self.listeners.values():
            listener.after_create_conversation(conversation)


    async def destroy_conversation(self, conversation_id: UUID, grace_period: int = 10) -> bool:
        response = await self.httpx_client.delete(f"{self.root_url}conversation/{conversation_id}")
        response_json = response.json
        return response_json
    
    async def shutdown(self, grace_period: int = 10):
        # Note: This does not shut down remote server...
        await self._httpx_client.aclose()
