from urllib.parse import parse_qs

import jwt
from socketio.exceptions import ConnectionRefusedError
# from sqlalchemy import select

from openhands.core.logger import openhands_logger as logger
from openhands.events.action import (
    NullAction,
)
from openhands.events.action.agent import RecallAction
from openhands.events.observation import (
    NullObservation,
)
from openhands.events.observation.agent import (
    AgentStateChangedObservation,
    RecallObservation,
)
from openhands.events.serialization import event_to_dict
from openhands.events.stream import AsyncEventStreamWrapper
from openhands.server.routes.auth import JWT_ALGORITHM, JWT_SECRET
from openhands.server.shared import (
    conversation_manager,
    sio,
)
# from openhands.server.db import database
# from openhands.server.models import User
from openhands.utils.get_user_setting import get_user_setting


@sio.event
async def connect(connection_id: str, environ):
    logger.info(f'sio:connect: {connection_id}')
    query_params = parse_qs(environ.get('QUERY_STRING', ''))
    latest_event_id = int(query_params.get('latest_event_id', [-1])[0])
    conversation_id = query_params.get('conversation_id', [None])[0]
    if not conversation_id:
        logger.error('No conversation_id in query params')
        raise ConnectionRefusedError('No conversation_id in query params')

    # Get JWT token from query params
    jwt_token = query_params.get('auth', [None])[0]
    if not jwt_token:
        logger.error('No JWT token provided')
        raise ConnectionRefusedError('Authentication required')

    try:
        # Verify and decode JWT token
        payload = jwt.decode(jwt_token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload['sub']
        logger.info(f'user_id: {user_id}')

        # Fetch user record from database
        # query = select(User).where(User.c.public_key == user_id.lower())
        # user = await database.fetch_one(query)
        # if not user:
        #     logger.error(f'User not found in database: {user_id}')
        #     raise ConnectionRefusedError('User not found')
            
        # logger.info(f'Found user record: {user["public_key"]}')
        # mnemonic = user['mnemonic']
        mnemonic = ''
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
    event_stream = await conversation_manager.join_conversation(
        conversation_id, connection_id, settings, user_id, github_user_id, mnemonic
    )
    logger.info(
        f'Connected to conversation {conversation_id} with connection_id {connection_id}. Replaying event stream...'
    )
    agent_state_changed = None
    if event_stream is None:
        raise ConnectionRefusedError('Failed to join conversation')
    async_stream = AsyncEventStreamWrapper(event_stream, latest_event_id + 1)
    async for event in async_stream:
        logger.debug(f'oh_event: {event.__class__.__name__}')
        if isinstance(
            event,
            (NullAction, NullObservation, RecallAction, RecallObservation),
        ):
            continue
        elif isinstance(event, AgentStateChangedObservation):
            agent_state_changed = event
        else:
            await sio.emit('oh_event', event_to_dict(event), to=connection_id)
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
