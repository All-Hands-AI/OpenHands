import json
import os
from types import MappingProxyType
from urllib.parse import parse_qs

import jwt
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
from openhands.server.modules import conversation_module
from openhands.server.shared import (
    ConversationStoreImpl,
    config,
    conversation_manager,
    sio,
)
from openhands.server.thesis_auth import (
    ThesisUser,
    UserStatus,
    get_user_detail_from_thesis_auth_server,
)
from openhands.storage.conversation.conversation_store import ConversationStore
from openhands.storage.data_models.conversation_metadata import ConversationMetadata
from openhands.utils.get_user_setting import get_user_setting


def create_provider_tokens_object(
    providers_set: list[ProviderType],
) -> PROVIDER_TOKEN_TYPE:
    provider_information = {}

    for provider in providers_set:
        provider_information[provider] = ProviderToken(token=None, user_id=None)

    return MappingProxyType(provider_information)


@sio.event
async def connect(connection_id: str, environ):
    logger.info(f'sio:connect: {connection_id}')
    query_params = parse_qs(environ.get('QUERY_STRING', ''))
    latest_event_id = int(query_params.get('latest_event_id', [-1])[0])
    conversation_id = query_params.get('conversation_id', [None])[0]
    system_prompt = query_params.get('system_prompt', [None])[0]
    user_prompt = query_params.get('user_prompt', [None])[0]
    mcp_disable = query_params.get('mcp_disable', [None])[0]
    x_device_id = query_params.get('x-device-id', [None])[0]
    # providers_raw: list[str] = query_params.get('providers_set', [])
    # providers_set: list[ProviderType] = [ProviderType(p) for p in providers_raw]

    user_id = None
    mnemonic = None
    conversation_configs = None
    conversation_metadata_result_set: ConversationMetadata | None = None
    conversation_store: ConversationStore | None = None

    if mcp_disable:
        mcp_disable = json.loads(mcp_disable)

    if not conversation_id:
        logger.error('No conversation_id in query params')
        raise ConnectionRefusedError('No conversation_id in query params')
    mode = query_params.get('mode', [None])[0]
    error, info = await conversation_module._get_conversation_visibility_info(
        conversation_id
    )
    conversation_configs = info
    print(f'Conversation configs: {conversation_configs}')

    # check if conversation_id is shared
    if mode == 'shared':
        if error:
            raise ConnectionRefusedError(error)
        else:
            user_id = str(info['user_id'])
            await conversation_module._update_research_view(
                conversation_id, environ.get('REMOTE_ADDR', '')
            )
    else:
        # Get JWT token from query params
        jwt_token = query_params.get('auth', [None])[0]

        # Check if conversation_id belongs to whitelisted user
        is_whitelisted = False
        whitelisted_user_id = os.getenv('USER_USE_CASE_SAMPLE')
        if jwt_token is None:
            conversation_store = await ConversationStoreImpl.get_instance(
                config, whitelisted_user_id, None
            )
            if not conversation_store:
                raise ConnectionRefusedError('Conversation store not found')
            conversation_metadata_result_set = await conversation_store.get_metadata(
                conversation_id
            )
            if (
                conversation_metadata_result_set
                and conversation_metadata_result_set.user_id == whitelisted_user_id
            ):
                is_whitelisted = True
                logger.info(
                    f'Whitelisted access for user {user_id} and conversation {conversation_id}'
                )

        if not is_whitelisted:
            # Normal authentication flow for non-whitelisted users/conversations
            if not jwt_token:
                logger.error('No JWT token provided')
                raise ConnectionRefusedError('Authentication required')

        try:
            if jwt_token is None:
                raise jwt.InvalidTokenError('No JWT token provided')

            user: ThesisUser | None = await get_user_detail_from_thesis_auth_server(
                'Bearer ' + jwt_token, x_device_id
            )
            if not user:
                logger.error(f'User not found in database: {user_id}')
                raise ConnectionRefusedError('User not found')

            user_id = user.publicAddress

            # TODO: If the user is not whitelisted and the run mode is DEV, skip the check
            if (
                user.whitelisted != UserStatus.WHITELISTED
                and os.getenv('RUN_MODE') != 'DEV'
            ):
                logger.error(f'User not activated: {user_id}')
                raise ConnectionRefusedError('User not activated')

            # TODO: if the user is whitelisted, check if the conversation is belong to the user
            conversation_store = await ConversationStoreImpl.get_instance(
                config, user_id, None
            )
            if not conversation_store:
                raise ConnectionRefusedError('Conversation store not found')
            conversation_metadata_result_set = await conversation_store.get_metadata(
                conversation_id
            )
            if not conversation_metadata_result_set or (
                conversation_metadata_result_set
                and conversation_metadata_result_set.user_id != user_id
            ):
                logger.error(f'Conversation not belong to the user: {conversation_id}')
                raise ConnectionRefusedError('This research isn’t available to you.')

            mnemonic = user.mnemonic
        except jwt.ExpiredSignatureError:
            logger.error('JWT token has expired')
            raise ConnectionRefusedError('Token has expired')
        except jwt.InvalidTokenError:
            logger.error('Invalid JWT token')
            raise ConnectionRefusedError('Invalid token')
        except Exception as e:
            logger.error(f'Error processing JWT token: {str(e)}')
            raise ConnectionRefusedError('Authentication failed')

    settings = await get_user_setting(user_id)

    if not settings:
        raise ConnectionRefusedError(
            'Settings not found', {'msg_id': 'CONFIGURATION$SETTINGS_NOT_FOUND'}
        )

    github_user_id = ''
    space_id = (
        conversation_configs.get('space_id', None) if conversation_configs else None
    )
    thread_follow_up = (
        conversation_configs.get('thread_follow_up', None)
        if conversation_configs
        else None
    )
    print(f'Space ID: {space_id}')
    print(f'Thread Follow Up: {thread_follow_up}')
    event_stream = await conversation_manager.join_conversation(
        conversation_id,
        connection_id,
        settings,
        user_id,
        github_user_id,
        mnemonic,
        system_prompt,
        user_prompt,
        mcp_disable,
        None,
        space_id,
        thread_follow_up,
    )
    logger.info(
        f'Connected to conversation {conversation_id} with connection_id {connection_id}. Replaying event stream...'
    )
    agent_state_changed = None
    if event_stream is None:
        raise ConnectionRefusedError('Failed to join conversation')
    async_store = AsyncEventStoreWrapper(event_stream, latest_event_id + 1)
    async for event in async_store:
        try:
            logger.debug(f'oh_event: {event.__class__.__name__}')
            if isinstance(
                event,
                (NullAction, NullObservation, RecallAction),
            ):
                continue
            elif isinstance(event, AgentStateChangedObservation):
                agent_state_changed = event
            else:
                event_dict = event_to_dict(event)
                logger.info(
                    f'Processing event: {event.__class__.__name__}, source: {event_dict.get("source")} in conversation {conversation_id}'
                )

                new_event_dict = {**event_dict, 'initialize_conversation': True}
                if (
                    mode == 'shared'
                    and new_event_dict.get('source') == 'user'
                    and conversation_configs is not None
                ):
                    hidden_prompt = conversation_configs.get('hidden_prompt', True)
                    new_event_dict['hidden_prompt'] = hidden_prompt
                    if hidden_prompt:
                        content = 'The creator of this prompt has chosen to keep it private, so it cannot be viewed by others unless its privacy settings are changed.'
                        new_event_dict.setdefault('args', {})['content'] = content
                        new_event_dict['message'] = content
                await sio.emit('oh_event', new_event_dict, to=connection_id)
        except Exception as e:
            logger.error(
                f'Error emitting event {event.__class__.__name__}: {str(e)} {conversation_id}'
            )
            continue

    if agent_state_changed:
        try:
            await sio.emit(
                'oh_event', event_to_dict(agent_state_changed), to=connection_id
            )
        except Exception as e:
            logger.error(
                f'Error emitting agent state change: {str(e)} {conversation_id}'
            )
    logger.info(f'Finished replaying event stream for conversation {conversation_id}')


@sio.event
async def oh_user_action(connection_id: str, data: dict):
    await conversation_manager.send_to_event_stream(connection_id, data)


@sio.event
async def oh_action(connection_id: str, data: dict):
    # TODO: Remove this handler once all clients are updated to use oh_user_action
    # Keeping for backward compatibility with in-progress sessions
    await conversation_manager.send_to_event_stream(connection_id, data)


@sio.event
async def disconnect(connection_id: str):
    logger.info(f'sio:disconnect:{connection_id}')
    await conversation_manager.disconnect_from_session(connection_id)
