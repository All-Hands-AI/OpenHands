from urllib.parse import parse_qs

import jwt
from pydantic import SecretStr
from socketio.exceptions import ConnectionRefusedError

from openhands.core.logger import openhands_logger as logger
from openhands.events.action import (
    NullAction,
)
from openhands.events.observation import (
    NullObservation,
)
from openhands.events.observation.agent import AgentStateChangedObservation
from openhands.events.serialization import event_to_dict
from openhands.events.stream import AsyncEventStreamWrapper
from openhands.server.shared import (
    ConversationStoreImpl,
    SettingsStoreImpl,
    config,
    conversation_manager,
    server_config,
    sio,
)
from openhands.server.types import AppMode


@sio.event
async def connect(connection_id: str, environ, auth):
    logger.info(f'sio:connect: {connection_id}')
    query_params = parse_qs(environ.get('QUERY_STRING', ''))
    latest_event_id = int(query_params.get('latest_event_id', [-1])[0])
    conversation_id = query_params.get('conversation_id', [None])[0]
    if not conversation_id:
        logger.error('No conversation_id in query params')
        raise ConnectionRefusedError('No conversation_id in query params')

    user_id = None
    if server_config.app_mode != AppMode.OSS:
        cookies_str = environ.get('HTTP_COOKIE', '')
        cookies = dict(cookie.split('=', 1) for cookie in cookies_str.split('; '))
        signed_token = cookies.get('openhands_auth', '')
        if not signed_token:
            logger.error('No openhands_auth cookie')
            raise ConnectionRefusedError('No openhands_auth cookie')
        if not config.jwt_secret:
            raise RuntimeError('JWT secret not found')

        jwt_secret = (
            config.jwt_secret.get_secret_value()
            if isinstance(config.jwt_secret, SecretStr)
            else config.jwt_secret
        )
        decoded = jwt.decode(signed_token, jwt_secret, algorithms=['HS256'])
        user_id = decoded['github_user_id']

        logger.info(f'User {user_id} is connecting to conversation {conversation_id}')

        conversation_store = await ConversationStoreImpl.get_instance(config, user_id)
        metadata = await conversation_store.get_metadata(conversation_id)

        if metadata.github_user_id != str(user_id):
            logger.error(
                f'User {user_id} is not allowed to join conversation {conversation_id}'
            )
            raise ConnectionRefusedError(
                f'User {user_id} is not allowed to join conversation {conversation_id}'
            )

    settings_store = await SettingsStoreImpl.get_instance(config, user_id)
    settings = await settings_store.load()

    if not settings:
        raise ConnectionRefusedError(
            'Settings not found', {'msg_id': 'CONFIGURATION$SETTINGS_NOT_FOUND'}
        )

    event_stream = await conversation_manager.join_conversation(
        conversation_id, connection_id, settings, user_id
    )

    agent_state_changed = None
    async_stream = AsyncEventStreamWrapper(event_stream, latest_event_id + 1)
    async for event in async_stream:
        if isinstance(
            event,
            (
                NullAction,
                NullObservation,
            ),
        ):
            continue
        elif isinstance(event, AgentStateChangedObservation):
            agent_state_changed = event
        else:
            await sio.emit('oh_event', event_to_dict(event), to=connection_id)
    if agent_state_changed:
        await sio.emit('oh_event', event_to_dict(agent_state_changed), to=connection_id)


@sio.event
async def oh_action(connection_id: str, data: dict):
    await conversation_manager.send_to_event_stream(connection_id, data)


@sio.event
async def disconnect(connection_id: str):
    logger.info(f'sio:disconnect:{connection_id}')
    await conversation_manager.disconnect_from_session(connection_id)
