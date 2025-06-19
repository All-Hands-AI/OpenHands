import asyncio
import os
from typing import Any
from urllib.parse import parse_qs

from socketio.exceptions import ConnectionRefusedError

from openhands.core.logger import openhands_logger as logger
from openhands.events.action import (
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
from openhands.events.serialization import event_to_dict
from openhands.integrations.service_types import ProviderType
from openhands.server.shared import (
    ConversationStoreImpl,
    SettingsStoreImpl,
    config,
    conversation_manager,
    sio,
)
from openhands.storage.conversation.conversation_validator import (
    create_conversation_validator,
)


async def verify_conversation_access(user_id: str | None, conversation_id: str) -> bool:
    """Verify that the user has access to the conversation.

    Args:
        user_id: The user ID
        conversation_id: The conversation ID

    Returns:
        True if user has access, False otherwise
    """
    try:
        # Check if conversation exists and user has access
        conversation_store = ConversationStoreImpl.get_instance()
        metadata = await conversation_store.get_metadata(conversation_id)

        # In multi-user mode, check if the conversation belongs to the user
        if user_id and hasattr(metadata, 'user_id'):
            return metadata.user_id == user_id

        # In single-user mode or if no user_id, allow access
        return True
    except Exception:
        return False


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

        logger.info(f'restrating session with providers: {providers_set}')

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

        # Verify user has access to the conversation
        has_access = await verify_conversation_access(user_id, conversation_id)
        if not has_access:
            raise ConnectionRefusedError('Access denied to conversation')

        # Get basic settings for websocket connection
        # The full conversation init data with providers will be set via the /start endpoint
        settings_store = await SettingsStoreImpl.get_instance(config, user_id)
        basic_settings = await settings_store.load()

        if not basic_settings:
            raise ConnectionRefusedError(
                'Settings not found', {'msg_id': 'CONFIGURATION$SETTINGS_NOT_FOUND'}
            )

        # Join the conversation with basic settings
        # The agent loop will be properly configured when /start endpoint is called
        agent_loop_info = await conversation_manager.join_conversation(
            conversation_id,
            connection_id,
            basic_settings,
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


def _invalid_session_api_key(query_params: dict[str, list[Any]]):
    session_api_key = os.getenv('SESSION_API_KEY')
    if not session_api_key:
        return False
    query_api_keys = query_params['session_api_key']
    if not query_api_keys:
        return True
    return query_api_keys[0] != session_api_key
