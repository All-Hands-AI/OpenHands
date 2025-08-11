import asyncio
import os
from typing import Any
from urllib.parse import parse_qs

from socketio.exceptions import ConnectionRefusedError

from openhands.core.logger import openhands_logger as logger
from openhands.events.action import (
    MessageAction,
    NullAction,
)
from openhands.events.action.agent import RecallAction
from openhands.events.async_event_store_wrapper import AsyncEventStoreWrapper
from openhands.events.event_store import EventStore
from openhands.events.observation import (
    NullObservation,
)
from openhands.events.observation.agent import (
    AgentStateChangedObservation,
)
from openhands.events.observation.user_chat import UserChatObservation
from openhands.events.serialization import event_to_dict
from openhands.integrations.service_types import ProviderType
from openhands.server.services.conversation_service import (
    setup_init_convo_settings,
)
from openhands.server.shared import (
    conversation_manager,
    sio,
)
from openhands.storage.conversation.conversation_validator import (
    create_conversation_validator,
)


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
        logger.info(
            f'Socket request for conversation {conversation_id} with connection_id {connection_id}'
        )
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
        logger.info(
            f'User {user_id} is allowed to connect to conversation {conversation_id}'
        )

        try:
            event_store = EventStore(
                conversation_id, conversation_manager.file_store, user_id
            )
        except FileNotFoundError as e:
            logger.error(
                f'Failed to create EventStore for conversation {conversation_id}: {e}'
            )
            raise ConnectionRefusedError(f'Failed to access conversation events: {e}')

        logger.info(
            f'Replaying event stream for conversation {conversation_id} with connection_id {connection_id}...'
        )
        agent_state_changed = None

        # Create an async store to replay events
        async_store = AsyncEventStoreWrapper(event_store, latest_event_id + 1)

        # Process all available events
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

        # Send the agent state changed event last if we have one
        if agent_state_changed:
            await sio.emit(
                'oh_event', event_to_dict(agent_state_changed), to=connection_id
            )

        logger.info(
            f'Finished replaying event stream for conversation {conversation_id}'
        )

        conversation_init_data = await setup_init_convo_settings(
            user_id, conversation_id, providers_set
        )

        agent_loop_info = await conversation_manager.join_conversation(
            conversation_id,
            connection_id,
            conversation_init_data,
            user_id,
        )

        if agent_loop_info is None:
            raise ConnectionRefusedError('Failed to join conversation')

        logger.info(
            f'Successfully joined conversation {conversation_id} with connection_id {connection_id}'
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


@sio.event
async def ai_chat(connection_id: str, data: dict[str, Any]) -> None:
    """Receives a chat message from the user, dispatches it to the agent, and streams back the response."""
    try:
        prompt = data['prompt']
        logger.info(
            f'Received chat message: {prompt} from connection_id: {connection_id}'
        )

        sid = conversation_manager._local_connection_id_to_session_id.get(
            connection_id
        )
        if not sid:
            logger.error(f'No session found for connection_id: {connection_id}')
            await sio.emit(
                'ai_chat_response',
                {'error': 'No active session found.'},
                to=connection_id,
            )
            return

        agent_session = conversation_manager.get_agent_session(sid)
        if not agent_session or not agent_session.controller:
            logger.error(f'No agent session or controller for sid: {sid}')
            await sio.emit(
                'ai_chat_response',
                {'error': 'Agent not initialized.'},
                to=connection_id,
            )
            return

        # The action to be dispatched
        action = MessageAction(prompt, source='user_chat')
        action_dict = event_to_dict(action)

        # Future to wait for the response
        future = asyncio.get_running_loop().create_future()

        # Define a one-time subscriber to catch the response
        def response_subscriber(event):
            if (
                isinstance(event, UserChatObservation)
                and event.cause == action.id
            ):
                future.set_result(event.content)
                # Clean up the subscriber
                agent_session.event_stream.unsubscribe('chat_response_listener')

        # Subscribe to the event stream
        agent_session.event_stream.subscribe(
            'chat_response_listener', response_subscriber
        )

        # Dispatch the action using the session's dispatch method
        current_session = conversation_manager._local_agent_loops_by_sid.get(sid)
        if not current_session:
            raise RuntimeError(f"Could not find session for sid: {sid}")
        await current_session.dispatch(action_dict)

        # Wait for the response from the subscriber
        try:
            response_content = await asyncio.wait_for(future, timeout=60.0)
            await sio.emit(
                'ai_chat_response',
                {'message': response_content},
                to=connection_id,
            )
        except asyncio.TimeoutError:
            logger.error(f'Timeout waiting for chat response for sid: {sid}')
            await sio.emit(
                'ai_chat_response',
                {'error': 'Request timed out.'},
                to=connection_id,
            )
            agent_session.event_stream.unsubscribe('chat_response_listener')

    except KeyError:
        logger.error(f'Missing "prompt" in chat message data: {data}')
        await sio.emit(
            'ai_chat_response',
            {'error': 'Invalid message format, "prompt" is required.'},
            to=connection_id,
        )
    except Exception as e:
        logger.exception(f'Error processing chat message: {e}')
        await sio.emit(
            'ai_chat_response',
            {'error': f'An internal error occurred: {e}'},
            to=connection_id,
        )


def _invalid_session_api_key(query_params: dict[str, list[Any]]):
    session_api_key = os.getenv('SESSION_API_KEY')
    if not session_api_key:
        return False
    query_api_keys = query_params['session_api_key']
    if not query_api_keys:
        return True
    return query_api_keys[0] != session_api_key
