
from fastapi import Request

from openhands.storage.conversation.conversation_store import ConversationStore
from openhands.server.shared import ConversationStoreImpl, config
from openhands.server.user_auth import get_user_auth
from openhands.integrations.provider import ProviderType


async def get_conversation_store(request: Request) -> ConversationStore:
    conversation_store: ConversationStore = getattr(request.state, 'conversation_store', None)
    if conversation_store:
        return conversation_store
    user_auth = await get_user_auth(request)
    user_id = await user_auth.get_user_id()
    provider_tokens = await user_auth.get_provider_tokens()
    github_token = provider_tokens.get(ProviderType.GITHUB)
    github_user_id = github_token.token.get_secret_value() if github_token else None
    conversation_store = await ConversationStoreImpl.get_instance(
        config, user_id, github_user_id
    )
    request.state.conversation_store = conversation_store
    return conversation_store
