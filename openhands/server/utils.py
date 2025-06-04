from fastapi import Depends, Request

from openhands.server.shared import ConversationStoreImpl, config, conversation_manager
from openhands.server.user_auth import get_user_auth, get_user_id
from openhands.storage.conversation.conversation_store import ConversationStore
from openhands.storage.data_models.settings import Settings


async def get_conversation_store(request: Request) -> ConversationStore | None:
    conversation_store: ConversationStore | None = getattr(
        request.state, 'conversation_store', None
    )
    if conversation_store:
        return conversation_store
    user_auth = await get_user_auth(request)
    user_id = await user_auth.get_user_id()
    conversation_store = await ConversationStoreImpl.get_instance(config, user_id)
    request.state.conversation_store = conversation_store
    return conversation_store


async def get_settings() -> Settings:
    """Get the settings for the current session.

    Returns:
        Settings: The settings for the current session.
    """
    return Settings.from_config() or Settings()


async def get_conversation(
    conversation_id: str, user_id: str | None = Depends(get_user_id)
):
    """Grabs conversation id set by middleware. Adds the conversation_id to the openapi schema."""
    conversation = await conversation_manager.attach_to_conversation(
        conversation_id, user_id
    )
    try:
        yield conversation
    finally:
        await conversation_manager.detach_from_conversation(conversation)
