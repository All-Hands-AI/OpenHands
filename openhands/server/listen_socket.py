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
from openhands.server.shared import session_manager, sio


@sio.event
async def connect(connection_id: str, environ):
    logger.info(f'sio:connect: {connection_id}')


@sio.event
async def oh_action(connection_id: str, data: dict):
    logger.info(f'sio:oh_action:{connection_id}')
    action = data.get('action', '')
    if action == 'connect':
        conversation_id = data.pop('conversation_id', None)
        latest_event_id = int(data.pop('latest_event_id', -1))
        event_stream = await session_manager.join_conversation(
            conversation_id, connection_id
        )
        return

    await session_manager.send_to_event_stream(connection_id, data)

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
