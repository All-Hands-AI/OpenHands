from typing import AsyncGenerator

from fastapi import Depends, Request

from openhands.server.session.conversation import ServerConversation
from openhands.server.shared import ConversationStoreImpl, config, conversation_manager
from openhands.server.user_auth import get_user_id
from openhands.storage.conversation.conversation_store import ConversationStore


async def get_conversation_store(request: Request) -> ConversationStore | None:
    conversation_store: ConversationStore | None = getattr(
        request.state, 'conversation_store', None
    )
    if conversation_store:
        return conversation_store
    user_id = get_user_id(request)
    conversation_store = await ConversationStoreImpl.get_instance(config, user_id)
    request.state.conversation_store = conversation_store
    return conversation_store


async def get_conversation(
    conversation_id: str, user_id: str | None = Depends(get_user_id)
) -> AsyncGenerator[ServerConversation | None, None]:
    """Grabs conversation id set by middleware. Adds the conversation_id to the openapi schema."""
    conversation = await conversation_manager.attach_to_conversation(
        conversation_id, user_id
    )
    try:
        yield conversation
    finally:
        if conversation is not None:
            await conversation_manager.detach_from_conversation(conversation)
