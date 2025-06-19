"""Utilities for conversation initialization."""

from types import MappingProxyType

from openhands.core.config.app_config import AppMode
from openhands.core.logger import openhands_logger as logger
from openhands.experiments.experiment_manager import ExperimentManagerImpl
from openhands.integrations.provider import PROVIDER_TOKEN_TYPE, ProviderToken
from openhands.integrations.service_types import ProviderType
from openhands.server.session.conversation_init_data import ConversationInitData
from openhands.server.shared import SecretsStoreImpl, SettingsStoreImpl, config
from openhands.storage.data_models.user_secrets import UserSecrets


def create_provider_tokens_object(
    providers_set: list[ProviderType],
) -> PROVIDER_TOKEN_TYPE:
    """Create provider tokens object for the given providers."""
    provider_information: dict[ProviderType, ProviderToken] = {}

    for provider in providers_set:
        provider_information[provider] = ProviderToken(token=None, user_id=None)

    return MappingProxyType(provider_information)


async def setup_init_convo_settings(
    user_id: str | None, conversation_id: str, providers_set: list[ProviderType]
) -> ConversationInitData:
    """Set up conversation initialization data with provider tokens.

    This function replicates the logic from listen_socket.py to ensure
    consistent conversation initialization between websocket and REST endpoints.

    Args:
        user_id: The user ID
        conversation_id: The conversation ID
        providers_set: List of provider types to set up tokens for

    Returns:
        ConversationInitData with provider tokens configured
    """
    settings_store = await SettingsStoreImpl.get_instance(config, user_id)
    settings = await settings_store.load()

    secrets_store = await SecretsStoreImpl.get_instance(config, user_id)
    user_secrets: UserSecrets | None = await secrets_store.load()

    if not settings:
        from socketio.exceptions import ConnectionRefusedError

        raise ConnectionRefusedError(
            'Settings not found', {'msg_id': 'CONFIGURATION$SETTINGS_NOT_FOUND'}
        )

    session_init_args: dict = {}
    session_init_args = {**settings.__dict__, **session_init_args}

    git_provider_tokens = create_provider_tokens_object(providers_set)
    logger.info(f'Git provider scaffold: {git_provider_tokens}')

    if config.app_mode != AppMode.SAAS and user_secrets:
        git_provider_tokens = user_secrets.provider_tokens

    session_init_args['git_provider_tokens'] = git_provider_tokens
    if user_secrets:
        session_init_args['custom_secrets'] = user_secrets.custom_secrets

    convo_init_data = ConversationInitData(**session_init_args)
    # We should recreate the same experiment conditions when restarting a conversation
    return ExperimentManagerImpl.run_conversation_variant_test(
        user_id, conversation_id, convo_init_data
    )
