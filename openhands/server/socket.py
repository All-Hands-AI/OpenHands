from fastapi import status

from openhands.core.logger import openhands_logger as logger
from openhands.core.schema.action import ActionType
from openhands.events.action import (
    NullAction,
)
from openhands.events.observation import (
    NullObservation,
)
from openhands.events.observation.agent import AgentStateChangedObservation
from openhands.events.serialization import event_to_dict
from openhands.events.stream import AsyncEventStreamWrapper
from openhands.server.auth import get_sid_from_token, sign_token
from openhands.server.github_utils import authenticate_github_user
from openhands.server.session.session_init_data import SessionInitData
from openhands.server.shared import config, session_manager, sio


@sio.event
async def connect(connection_id: str, environ):
    logger.info(f'sio:connect: {connection_id}')


@sio.event
async def oh_action(connection_id: str, data: dict):
    # If it's an init, we do it here.
    action = data.get('action', '')
    if action == ActionType.INIT:
        token = data.pop('token', None)
        github_token = data.pop('github_token', None)
        latest_event_id = int(data.pop('latest_event_id', -1))
        kwargs = {k.lower(): v for k, v in (data.get('args') or {}).items()}
        session_init_data = SessionInitData(**kwargs)
        session_init_data.github_token = github_token
        await init_connection(
            connection_id, token, github_token, session_init_data, latest_event_id
        )
        return

    logger.info(f'sio:oh_action:{connection_id}')
    await session_manager.send_to_event_stream(connection_id, data)


async def init_connection(
    connection_id: str,
    token: str | None,
    gh_token: str | None,
    session_init_data: SessionInitData,
    latest_event_id: int,
):
    if not await authenticate_github_user(gh_token):
        raise RuntimeError(status.WS_1008_POLICY_VIOLATION)

    if token:
        sid = get_sid_from_token(token, config.jwt_secret)
        if sid == '':
            await sio.emit('oh_event', {'error': 'Invalid token', 'error_code': 401})
            return
        logger.info(f'Existing session: {sid}')
    else:
        sid = connection_id
        logger.info(f'New session: {sid}')

    token = sign_token({'sid': sid}, config.jwt_secret)
    await sio.emit('oh_event', {'token': token, 'status': 'ok'}, to=connection_id)

    # The session in question should exist, but may not actually be running locally...
    event_stream = await session_manager.init_or_join_session(
        sid, connection_id, session_init_data
    )

    # Send events
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
            continue
        await sio.emit('oh_event', event_to_dict(event), to=connection_id)
    if agent_state_changed:
        await sio.emit('oh_event', event_to_dict(agent_state_changed), to=connection_id)


@sio.event
async def disconnect(connection_id: str):
    logger.info(f'sio:disconnect:{connection_id}')
    await session_manager.disconnect_from_session(connection_id)
