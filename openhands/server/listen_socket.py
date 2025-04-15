import os
from types import MappingProxyType
from urllib.parse import parse_qs

import jwt
from socketio.exceptions import ConnectionRefusedError
from sqlalchemy import select

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
from openhands.server.db import database
from openhands.server.models import User
from openhands.server.routes.auth import JWT_ALGORITHM, JWT_SECRET
from openhands.server.shared import (
    ConversationStoreImpl,
    config,
    conversation_manager,
    sio,
)
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
    # providers_raw: list[str] = query_params.get('providers_set', [])
    # providers_set: list[ProviderType] = [ProviderType(p) for p in providers_raw]

    if not conversation_id:
        logger.error('No conversation_id in query params')
        raise ConnectionRefusedError('No conversation_id in query params')

    # Get JWT token from query params
    jwt_token = query_params.get('auth', [None])[0]
    user_id = None
    mnemonic = None

    # Check if conversation_id belongs to whitelisted user
    is_whitelisted = False
    whitelisted_user_id = os.getenv('USER_USE_CASE_SAMPLE')
    if jwt_token is None:
        conversation_store = await ConversationStoreImpl.get_instance(
            config, whitelisted_user_id, None
        )
        conversation_metadata_result_set = await conversation_store.get_metadata(
            conversation_id
        )
        if conversation_metadata_result_set.user_id == whitelisted_user_id:
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
            # Verify and decode JWT token
            payload = jwt.decode(jwt_token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            user_id = payload['sub']
            logger.info(f'user_id: {user_id}')

            # Fetch user record from database
            query = select(User).where(User.c.public_key == user_id.lower())
            user = await database.fetch_one(query)
            if not user:
                logger.error(f'User not found in database: {user_id}')
                raise ConnectionRefusedError('User not found')

            logger.info(f'Found user record: {user["public_key"]}')
            mnemonic = user['mnemonic']
        except jwt.ExpiredSignatureError:
            logger.error('JWT token has expired')
            raise ConnectionRefusedError('Token has expired')
        except jwt.InvalidTokenError:
            logger.error('Invalid JWT token')
            raise ConnectionRefusedError('Invalid token')
        except Exception as e:
            logger.error(f'Error processing JWT token: {str(e)}')
            raise ConnectionRefusedError('Authentication failed')

    # TODO FIXME: Logic from upstream. Temporarily comment out. Need to check if they are useful
    # cookies_str = environ.get('HTTP_COOKIE', '')
    # conversation_validator = create_conversation_validator()
    # user_id, github_user_id = await conversation_validator.validate(
    #     conversation_id, cookies_str
    # )

    settings = await get_user_setting(user_id)

    if not settings:
        raise ConnectionRefusedError(
            'Settings not found', {'msg_id': 'CONFIGURATION$SETTINGS_NOT_FOUND'}
        )

    # TODO FIXME: code from upstream. Should consider checking if do we need to use this.
    # session_init_args: dict = {}
    # if settings:
    #     session_init_args = {**settings.__dict__, **session_init_args}

    # session_init_args['git_provider_tokens'] = create_provider_tokens_object(
    #     providers_set
    # )
    # conversation_init_data = ConversationInitData(**session_init_args)

    github_user_id = ''
    event_stream = await conversation_manager.join_conversation(
        conversation_id, connection_id, settings, user_id, github_user_id, mnemonic
    )
    logger.info(
        f'Connected to conversation {conversation_id} with connection_id {connection_id}. Replaying event stream...'
    )
    agent_state_changed = None
    if event_stream is None:
        raise ConnectionRefusedError('Failed to join conversation')
    async_store = AsyncEventStoreWrapper(event_stream, latest_event_id + 1)
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
            event_dict = event_to_dict(event)
            await sio.emit('oh_event', {**event_dict, 'initialize_conversation': True}, to=connection_id)
    if agent_state_changed:
        await sio.emit('oh_event', event_to_dict(agent_state_changed), to=connection_id)
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
