"""Transport-neutral helpers for conversation operations.

This module provides utilities that can be used by both server and CLI
without importing FastAPI or socket.io. It centralizes shared logic used to
inspect and attach to conversations.
"""

import uuid
from typing import Optional

from openhands.conversation.conversation import Conversation
from openhands.core.config.openhands_config import OpenHandsConfig
from openhands.events.stream import EventStream
from openhands.storage import get_file_store
from openhands.storage.conversation.conversation_store import ConversationStore
from openhands.storage.conversation.file_conversation_store import (
    FileConversationStore,
)
from openhands.storage.data_models.conversation_metadata import ConversationMetadata


async def get_conversation_store(
    config: OpenHandsConfig, user_id: Optional[str]
) -> ConversationStore:
    """Return a conversation store instance for the given user.

    This neutral helper defaults to the FileConversationStore, which works in
    headless/CLI contexts without importing server-side wiring.
    """
    file_store = get_file_store(
        file_store_type=config.file_store,
        file_store_path=config.file_store_path,
        file_store_web_hook_url=config.file_store_web_hook_url,
        file_store_web_hook_headers=config.file_store_web_hook_headers,
        file_store_web_hook_batch=config.file_store_web_hook_batch,
    )
    return FileConversationStore(file_store)


async def generate_unique_conversation_id(store: ConversationStore) -> str:
    """Generate a unique conversation id not present in the store."""
    conversation_id = uuid.uuid4().hex
    while await store.exists(conversation_id):
        conversation_id = uuid.uuid4().hex
    return conversation_id


async def get_conversation_metadata(
    store: ConversationStore, conversation_id: str
) -> ConversationMetadata:
    """Retrieve conversation metadata or raise FileNotFoundError."""
    return await store.get_metadata(conversation_id)


def get_event_stream(
    config: OpenHandsConfig, sid: str, user_id: Optional[str] = None
) -> EventStream:
    """Build a minimal EventStream from config to tail events."""
    file_store = get_file_store(
        file_store_type=config.file_store,
        file_store_path=config.file_store_path,
        file_store_web_hook_url=config.file_store_web_hook_url,
        file_store_web_hook_headers=config.file_store_web_hook_headers,
        file_store_web_hook_batch=config.file_store_web_hook_batch,
    )
    return EventStream(sid, file_store, user_id)


def attach_to_conversation(
    config: OpenHandsConfig, sid: str, user_id: Optional[str] = None
) -> Conversation:
    """Create a Conversation facade attached to an existing session.

    Does not connect or start any runtime; caller may call connect() if needed.
    """
    file_store = get_file_store(
        file_store_type=config.file_store,
        file_store_path=config.file_store_path,
        file_store_web_hook_url=config.file_store_web_hook_url,
        file_store_web_hook_headers=config.file_store_web_hook_headers,
        file_store_web_hook_batch=config.file_store_web_hook_batch,
    )
    return Conversation(
        sid,
        file_store,
        config,
        user_id,
        headless_mode=True,
        attach_to_existing=True,
    )
