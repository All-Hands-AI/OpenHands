import uuid

from fastapi import Depends, HTTPException, Request, status

from openhands.core.logger import openhands_logger as logger
from openhands.server.shared import ConversationStoreImpl, config, conversation_manager
from openhands.server.user_auth import get_user_id
from openhands.storage.conversation.conversation_store import ConversationStore


async def get_conversation_store(request: Request) -> ConversationStore | None:
    conversation_store: ConversationStore | None = getattr(
        request.state, 'conversation_store', None
    )
    if conversation_store:
        return conversation_store
    user_id = await get_user_id(request)
    conversation_store = await ConversationStoreImpl.get_instance(config, user_id)
    request.state.conversation_store = conversation_store
    return conversation_store


async def generate_unique_conversation_id(
    conversation_store: ConversationStore,
) -> str:
    conversation_id = uuid.uuid4().hex
    while await conversation_store.exists(conversation_id):
        conversation_id = uuid.uuid4().hex
    return conversation_id


async def get_conversation(
    conversation_id: str, user_id: str | None = Depends(get_user_id)
):
    """Grabs conversation id set by middleware. Adds the conversation_id to the openapi schema."""
    conversation = await conversation_manager.attach_to_conversation(
        conversation_id, user_id
    )
    if not conversation:
        logger.warning(
            f'get_conversation: conversation {conversation_id} not found, attach_to_conversation returned None',
            extra={'session_id': conversation_id, 'user_id': user_id},
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'Conversation {conversation_id} not found',
        )
    try:
        yield conversation
    finally:
        await conversation_manager.detach_from_conversation(conversation)
