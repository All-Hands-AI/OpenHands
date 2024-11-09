import asyncio
import uuid
from fastapi import WebSocket, status
from openhands.server.auth.auth import get_sid_from_token, sign_token
from openhands.server.github import authenticate_github_user
from openhands.events.stream import AsyncEventStreamWrapper
from openhands.events.serialization import event_to_dict
from openhands.events.action import (
    ChangeAgentStateAction,
    NullAction,
)
from openhands.events.observation import (
    AgentStateChangedObservation,
    NullObservation,
)
from openhands.core.logger import openhands_logger as logger

async def websocket_endpoint(websocket: WebSocket, session_manager, config):
    protocols = websocket.headers.get('sec-websocket-protocol', '').split(', ')
    if len(protocols) < 3:
        logger.error('Expected 3 websocket protocols, got %d', len(protocols))
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    real_protocol = protocols[0]
    jwt_token = protocols[1] if protocols[1] != 'NO_JWT' else ''
    github_token = protocols[2] if protocols[2] != 'NO_GITHUB' else ''

    if not await authenticate_github_user(github_token):
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await asyncio.wait_for(websocket.accept(subprotocol=real_protocol), 10)

    if jwt_token:
        sid = get_sid_from_token(jwt_token, config.jwt_secret)
        if sid == '':
            await websocket.send_json({'error': 'Invalid token', 'error_code': 401})
            await websocket.close()
            return
    else:
        sid = str(uuid.uuid4())
        jwt_token = sign_token({'sid': sid}, config.jwt_secret)

    logger.info(f'New session: {sid}')
    session = session_manager.add_or_restart_session(sid, websocket)
    await websocket.send_json({'token': jwt_token, 'status': 'ok'})

    latest_event_id = -1
    if websocket.query_params.get('latest_event_id'):
        latest_event_id = int(websocket.query_params.get('latest_event_id'))

    async_stream = AsyncEventStreamWrapper(
        session.agent_session.event_stream, latest_event_id + 1
    )

    async for event in async_stream:
        if isinstance(
            event,
            (
                NullAction,
                NullObservation,
                ChangeAgentStateAction,
                AgentStateChangedObservation,
            ),
        ):
            continue
        await websocket.send_json(event_to_dict(event))

    await session.loop_recv()
