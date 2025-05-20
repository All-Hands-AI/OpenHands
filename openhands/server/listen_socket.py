import asyncio
import os
from types import MappingProxyType
from typing import Any
from urllib.parse import parse_qs

from socketio.exceptions import ConnectionRefusedError

from openhands.core.logger import openhands_logger as logger
from openhands.events.action import (
    NullAction,
)
from openhands.events.action.agent import RecallAction
from openhands.events.async_event_store_wrapper import AsyncEventStoreWrapper
from openhands.events.observation import (
    NullObservation,
)
from openhands.events.observation.agent import (
    AgentStateChangedObservation,
)
from openhands.events.serialization import event_to_dict
from openhands.integrations.provider import PROVIDER_TOKEN_TYPE, ProviderToken
from openhands.integrations.service_types import ProviderType
from openhands.server.session.conversation_init_data import ConversationInitData
from openhands.server.shared import (
    SecretsStoreImpl,
    SettingsStoreImpl,
    config,
    conversation_manager,
    server_config,
    sio,
)
from openhands.server.types import AppMode
from openhands.storage.conversation.conversation_validator import (
    create_conversation_validator,
)
from openhands.storage.data_models.user_secrets import UserSecrets


def create_provider_tokens_object(
    providers_set: list[ProviderType],
) -> PROVIDER_TOKEN_TYPE:
    provider_information: dict[ProviderType, ProviderToken] = {}

    for provider in providers_set:
        provider_information[provider] = ProviderToken(token=None, user_id=None)

    return MappingProxyType(provider_information)


@sio.event
async def connect(connection_id: str, environ: dict) -> None:
    try:
        logger.info(f'sio:connect: {connection_id}')
        query_params = parse_qs(environ.get('QUERY_STRING', ''))
        latest_event_id_str = query_params.get('latest_event_id', [-1])[0]
        try:
            latest_event_id = int(latest_event_id_str)
        except ValueError:
            logger.debug(
                f'Invalid latest_event_id value: {latest_event_id_str}, defaulting to -1'
            )
            latest_event_id = -1
        conversation_id = query_params.get('conversation_id', [None])[0]
        raw_list = query_params.get('providers_set', [])
        providers_list = []
        for item in raw_list:
            providers_list.extend(item.split(',') if isinstance(item, str) else [])
        providers_list = [p for p in providers_list if p]
        providers_set = [ProviderType(p) for p in providers_list]

        if not conversation_id:
            logger.error('No conversation_id in query params')
            raise ConnectionRefusedError('No conversation_id in query params')

        if _invalid_session_api_key(query_params):
            raise ConnectionRefusedError('invalid_session_api_key')

        cookies_str = environ.get('HTTP_COOKIE', '')
        # Get Authorization header from the environment
        # Headers in WSGI/ASGI are prefixed with 'HTTP_' and have dashes replaced with underscores
        authorization_header = environ.get('HTTP_AUTHORIZATION', None)
        conversation_validator = create_conversation_validator()
        user_id = await conversation_validator.validate(
            conversation_id, cookies_str, authorization_header
        )

        settings_store = await SettingsStoreImpl.get_instance(config, user_id)
        settings = await settings_store.load()

        secrets_store = await SecretsStoreImpl.get_instance(config, user_id)
        user_secrets: UserSecrets | None = await secrets_store.load()

        if not settings:
            raise ConnectionRefusedError(
                'Settings not found', {'msg_id': 'CONFIGURATION$SETTINGS_NOT_FOUND'}
            )
        session_init_args: dict = {}
        if settings:
            session_init_args = {**settings.__dict__, **session_init_args}

        git_provider_tokens = create_provider_tokens_object(providers_set)
        if server_config.app_mode != AppMode.SAAS and user_secrets:
            git_provider_tokens = user_secrets.provider_tokens

        session_init_args['git_provider_tokens'] = git_provider_tokens
        if user_secrets:
            session_init_args['custom_secrets'] = user_secrets.custom_secrets

        conversation_init_data = ConversationInitData(**session_init_args)

        agent_loop_info = await conversation_manager.join_conversation(
            conversation_id,
            connection_id,
            conversation_init_data,
            user_id,
        )
        logger.info(
            f'Connected to conversation {conversation_id} with connection_id {connection_id}. Replaying event stream...'
        )
        agent_state_changed = None
        if agent_loop_info is None:
            raise ConnectionRefusedError('Failed to join conversation')
        async_store = AsyncEventStoreWrapper(
            agent_loop_info.event_store, latest_event_id + 1
        )
        async for event in async_store:
            logger.debug(f'oh_event: {event.__class__.__name__}')
            if isinstance(
                event,
                (NullAction, NullObservation, RecallAction),
            ):
                continue
            elif isinstance(event, AgentStateChangedObservation):
                agent_state_changed = event
            else:
                await sio.emit('oh_event', event_to_dict(event), to=connection_id)
        if agent_state_changed:
            await sio.emit(
                'oh_event', event_to_dict(agent_state_changed), to=connection_id
            )
        logger.info(
            f'Finished replaying event stream for conversation {conversation_id}'
        )
    except ConnectionRefusedError:
        # Close the broken connection after sending an error message
        asyncio.create_task(sio.disconnect(connection_id))
        raise


@sio.event
async def oh_user_action(connection_id: str, data: dict[str, Any]) -> None:
    await conversation_manager.send_to_event_stream(connection_id, data)


@sio.event
async def oh_action(connection_id: str, data: dict[str, Any]) -> None:
    # TODO: Remove this handler once all clients are updated to use oh_user_action
    # Keeping for backward compatibility with in-progress sessions
    await conversation_manager.send_to_event_stream(connection_id, data)


@sio.event
async def disconnect(connection_id: str) -> None:
    logger.info(f'sio:disconnect:{connection_id}')
    await conversation_manager.disconnect_from_session(connection_id)


def _invalid_session_api_key(query_params: dict[str, list[Any]]):
    session_api_key = os.getenv('SESSION_API_KEY')
    if not session_api_key:
        return False
    query_api_keys = query_params['session_api_key']
    if not query_api_keys:
        return True
    return query_api_keys[0] != session_api_key
