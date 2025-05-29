import uuid

from fastapi import Request

from openhands.server.session.conversation import ServerConversation
from openhands.server.shared import ConversationStoreImpl, config
from openhands.server.user_auth import get_user_auth
from openhands.storage.conversation.conversation_store import ConversationStore


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


def get_conversation_state(request: Request) -> ServerConversation | None:
    """
    Get the conversation object from the request state.

    Args:
        request: The FastAPI request object.

    Returns:
        The conversation object.
    """
    conversation = getattr(request.state, 'conversation', None)
    return conversation


async def generate_unique_conversation_id(
    conversation_store: ConversationStore,
) -> str:
    conversation_id = uuid.uuid4().hex
    while await conversation_store.exists(conversation_id):
        conversation_id = uuid.uuid4().hex
    return conversation_id
