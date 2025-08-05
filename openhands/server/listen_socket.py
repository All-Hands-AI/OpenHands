import asyncio
import os
import time
from typing import Any
from urllib.parse import parse_qs

from socketio.exceptions import ConnectionRefusedError

from openhands.core.logger import openhands_logger as logger
from openhands.server.websocket.logging import (
    CorrelationIdManager,
    log_websocket_connection,
    log_websocket_error,
    log_websocket_event,
    log_websocket_metrics,
)
from openhands.server.websocket.error_responses import (
    WebSocketErrorCode,
    WebSocketErrorEmitter,
    WebSocketErrorResponseBuilder,
)
from openhands.server.websocket.connection_state import (
    ConnectionStateManager,
)
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
from openhands.server.services.conversation_service import (
    setup_init_convo_settings,
)
from openhands.server.shared import (
    conversation_manager,
    sio,
)

# Initialize error emitter for standardized error responses
error_emitter = WebSocketErrorEmitter(sio)

# Initialize connection state manager
redis_host = os.environ.get('REDIS_HOST')
redis_password = os.environ.get('REDIS_PASSWORD')
if redis_host:
    redis_url = f'redis://{redis_host}'
    connection_state_manager = ConnectionStateManager(redis_url, redis_password)
else:
    # Fallback to localhost Redis for development
    connection_state_manager = ConnectionStateManager()

from openhands.storage.conversation.conversation_validator import (
    create_conversation_validator,
)


@sio.event
async def connect(connection_id: str, environ: dict) -> None:
    start_time = time.time()

    # Generate correlation ID for this connection request
    with CorrelationIdManager.correlation_context() as correlation_id:
        try:
            log_websocket_connection(
                event_type="connect_attempt",
                message=f"WebSocket connection attempt",
                connection_id=connection_id,
                client_info={
                    "user_agent": environ.get('HTTP_USER_AGENT', 'unknown'),
                    "remote_addr": environ.get('REMOTE_ADDR', 'unknown'),
                    "query_string": environ.get('QUERY_STRING', '')
                }
            )

            query_params = parse_qs(environ.get('QUERY_STRING', ''))
            latest_event_id_str = query_params.get('latest_event_id', [-1])[0]
            try:
                latest_event_id = int(latest_event_id_str)
            except ValueError:
                log_websocket_error(
                    error_type="invalid_parameter",
                    message=f'Invalid latest_event_id value: {latest_event_id_str}, defaulting to -1',
                    connection_id=connection_id,
                    error_details={"parameter": "latest_event_id", "value": latest_event_id_str},
                    level="warning"
                )
                latest_event_id = -1

            conversation_id = query_params.get('conversation_id', [None])[0]

            log_websocket_connection(
                event_type="connect_request",
                message=f"Socket connection request for conversation {conversation_id}",
                connection_id=connection_id,
                conversation_id=conversation_id,
                latest_event_id=latest_event_id
            )

            raw_list = query_params.get('providers_set', [])
            providers_list = []
            for item in raw_list:
                providers_list.extend(item.split(',') if isinstance(item, str) else [])
            providers_list = [p for p in providers_list if p]
            providers_set = [ProviderType(p) for p in providers_list]

            if not conversation_id:
                error_response = WebSocketErrorResponseBuilder.create_error_response(
                    WebSocketErrorCode.INVALID_CONNECTION_PARAMS,
                    "Missing required parameter: conversation_id",
                    correlation_id=correlation_id,
                    details={"parameter": "conversation_id", "query_params": list(query_params.keys())}
                )

                log_websocket_error(
                    error_type="missing_parameter",
                    message="No conversation_id in query params",
                    connection_id=connection_id,
                    error_details={"parameter": "conversation_id", "query_params": list(query_params.keys())}
                )

                await error_emitter.emit_error_and_disconnect(connection_id, error_response)
                raise ConnectionRefusedError('No conversation_id in query params')

            if _invalid_session_api_key(query_params):
                error_response = WebSocketErrorResponseBuilder.create_error_response(
                    WebSocketErrorCode.INVALID_SESSION_KEY,
                    "Invalid or missing session API key",
                    correlation_id=correlation_id,
                    details={"reason": "invalid_session_api_key"}
                )

                log_websocket_error(
                    error_type="authentication",
                    message="Invalid session API key",
                    connection_id=connection_id,
                    conversation_id=conversation_id,
                    error_details={"reason": "invalid_session_api_key"}
                )

                await error_emitter.emit_error_and_disconnect(connection_id, error_response)
                raise ConnectionRefusedError('invalid_session_api_key')

            cookies_str = environ.get('HTTP_COOKIE', '')
            # Get Authorization header from the environment
            # Headers in WSGI/ASGI are prefixed with 'HTTP_' and have dashes replaced with underscores
            authorization_header = environ.get('HTTP_AUTHORIZATION', None)
            conversation_validator = create_conversation_validator()

            try:
                user_id = await conversation_validator.validate(
                    conversation_id, cookies_str, authorization_header
                )
                log_websocket_connection(
                    event_type="authentication_success",
                    message=f"User {user_id} authenticated for conversation {conversation_id}",
                    connection_id=connection_id,
                    user_id=user_id,
                    conversation_id=conversation_id
                )

                # Create connection state tracking
                try:
                    client_info = {
                        "user_agent": environ.get('HTTP_USER_AGENT', 'unknown'),
                        "remote_addr": environ.get('REMOTE_ADDR', 'unknown'),
                        "query_string": environ.get('QUERY_STRING', ''),
                        "providers_set": providers_list,
                    }
                    await connection_state_manager.create_connection_state(
                        connection_id=connection_id,
                        user_id=user_id,
                        conversation_id=conversation_id,
                        client_info=client_info,
                        last_event_id=latest_event_id
                    )
                    logger.info(
                        f"Created connection state tracking for {connection_id}",
                        extra={
                            "connection_id": connection_id,
                            "user_id": user_id,
                            "conversation_id": conversation_id
                        }
                    )
                except Exception as state_error:
                    # Don't fail the connection if state tracking fails, just log it
                    logger.warning(
                        f"Failed to create connection state tracking for {connection_id}: {state_error}",
                        extra={
                            "connection_id": connection_id,
                            "user_id": user_id,
                            "conversation_id": conversation_id,
                            "error": str(state_error)
                        }
                    )
            except Exception as e:
                error_response = WebSocketErrorResponseBuilder.authentication_failed(
                    f"Authentication failed: {str(e)}",
                    correlation_id=correlation_id,
                    details={"exception": str(e), "type": type(e).__name__}
                )

                log_websocket_error(
                    error_type="authentication",
                    message=f"Authentication failed: {str(e)}",
                    connection_id=connection_id,
                    conversation_id=conversation_id,
                    error_details={"exception": str(e), "type": type(e).__name__}
                )

                await error_emitter.emit_error_and_disconnect(connection_id, error_response)
                raise ConnectionRefusedError(f'Authentication failed: {str(e)}')

            try:
                event_store = EventStore(
                    conversation_id, conversation_manager.file_store, user_id
                )
            except FileNotFoundError as e:
                error_response = WebSocketErrorResponseBuilder.conversation_not_found(
                    f"Conversation not found or inaccessible: {conversation_id}",
                    correlation_id=correlation_id,
                    details={"conversation_id": conversation_id, "exception": str(e)}
                )

                log_websocket_error(
                    error_type="event_store",
                    message=f"Failed to create EventStore for conversation {conversation_id}: {e}",
                    connection_id=connection_id,
                    user_id=user_id,
                    conversation_id=conversation_id,
                    error_details={"exception": str(e), "type": "FileNotFoundError"}
                )

                await error_emitter.emit_error_and_disconnect(connection_id, error_response)
                raise ConnectionRefusedError(f'Failed to access conversation events: {e}')

            log_websocket_event(
                event_type="event_replay_start",
                message=f"Starting event replay for conversation {conversation_id}",
                connection_id=connection_id,
                user_id=user_id,
                conversation_id=conversation_id,
                event_data={"latest_event_id": latest_event_id}
            )

            agent_state_changed = None
            events_replayed = 0

            # Create an async store to replay events
            async_store = AsyncEventStoreWrapper(event_store, latest_event_id + 1)

            # Process all available events
            async for event in async_store:
                log_websocket_event(
                    event_type="event_replay",
                    message=f"Replaying event: {event.__class__.__name__}",
                    connection_id=connection_id,
                    user_id=user_id,
                    conversation_id=conversation_id,
                    event_data={"event_type": event.__class__.__name__},
                    level="debug"
                )

                if isinstance(
                    event,
                    (NullAction, NullObservation, RecallAction),
                ):
                    continue
                elif isinstance(event, AgentStateChangedObservation):
                    agent_state_changed = event
                else:
                    await sio.emit('oh_event', event_to_dict(event), to=connection_id)
                    events_replayed += 1

            # Send the agent state changed event last if we have one
            if agent_state_changed:
                await sio.emit(
                    'oh_event', event_to_dict(agent_state_changed), to=connection_id
                )
                events_replayed += 1

            log_websocket_event(
                event_type="event_replay_complete",
                message=f"Finished replaying {events_replayed} events for conversation {conversation_id}",
                connection_id=connection_id,
                user_id=user_id,
                conversation_id=conversation_id,
                event_data={"events_replayed": events_replayed}
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
                error_response = WebSocketErrorResponseBuilder.create_error_response(
                    WebSocketErrorCode.INVALID_CONVERSATION_STATE,
                    "Failed to join conversation - conversation may be in an invalid state",
                    correlation_id=correlation_id,
                    details={"reason": "agent_loop_info_none", "conversation_id": conversation_id}
                )

                log_websocket_error(
                    error_type="conversation_join",
                    message="Failed to join conversation",
                    connection_id=connection_id,
                    user_id=user_id,
                    conversation_id=conversation_id,
                    error_details={"reason": "agent_loop_info_none"}
                )

                await error_emitter.emit_error_and_disconnect(connection_id, error_response)
                raise ConnectionRefusedError('Failed to join conversation')

            connection_time_ms = (time.time() - start_time) * 1000
            log_websocket_connection(
                event_type="connect_success",
                message=f"Successfully connected to conversation {conversation_id}",
                connection_id=connection_id,
                user_id=user_id,
                conversation_id=conversation_id,
                connection_time_ms=connection_time_ms,
                events_replayed=events_replayed
            )

            # Log connection metrics
            log_websocket_metrics(
                metric_type="connection",
                message="Connection established successfully",
                connection_id=connection_id,
                user_id=user_id,
                conversation_id=conversation_id,
                metrics={
                    "connection_time_ms": connection_time_ms,
                    "events_replayed": events_replayed,
                    "latest_event_id": latest_event_id
                }
            )

        except ConnectionRefusedError as e:
            connection_time_ms = (time.time() - start_time) * 1000
            log_websocket_error(
                error_type="connection_refused",
                message=f"Connection refused: {str(e)}",
                connection_id=connection_id,
                user_id=locals().get('user_id'),
                conversation_id=locals().get('conversation_id'),
                error_details={
                    "reason": str(e),
                    "connection_time_ms": connection_time_ms
                }
            )
            # Error response already sent by specific handlers above
            # Close the broken connection after sending an error message
            asyncio.create_task(sio.disconnect(connection_id))
            raise
        except Exception as e:
            connection_time_ms = (time.time() - start_time) * 1000

            error_response = WebSocketErrorResponseBuilder.internal_server_error(
                f"Unexpected error during connection: {str(e)}",
                correlation_id=correlation_id,
                details={
                    "exception": str(e),
                    "type": type(e).__name__,
                    "connection_time_ms": connection_time_ms
                }
            )

            log_websocket_error(
                error_type="unexpected_error",
                message=f"Unexpected error during connection: {str(e)}",
                connection_id=connection_id,
                user_id=locals().get('user_id'),
                conversation_id=locals().get('conversation_id'),
                error_details={
                    "exception": str(e),
                    "type": type(e).__name__,
                    "connection_time_ms": connection_time_ms
                }
            )

            await error_emitter.emit_error_and_disconnect(connection_id, error_response)
            raise ConnectionRefusedError(f'Unexpected error: {str(e)}')


@sio.event
async def oh_user_action(connection_id: str, data: dict[str, Any]) -> None:
    start_time = time.time()

    # Use existing correlation ID if available, or generate a new one
    correlation_id = CorrelationIdManager.get_correlation_id()
    if not correlation_id:
        correlation_id = CorrelationIdManager.generate_correlation_id()
        CorrelationIdManager.set_correlation_id(correlation_id)

    log_websocket_event(
        event_type="user_action_received",
        message="Received user action event",
        connection_id=connection_id,
        event_data=data,
        level="debug"
    )

    try:
        await conversation_manager.send_to_event_stream(connection_id, data)

        processing_time_ms = (time.time() - start_time) * 1000
        log_websocket_event(
            event_type="user_action_processed",
            message="User action processed successfully",
            connection_id=connection_id,
            processing_time_ms=processing_time_ms,
            level="debug"
        )

        # Update connection activity
        try:
            await connection_state_manager.update_last_activity(connection_id)
        except Exception as state_error:
            # Don't fail the action if state update fails, just log it
            logger.debug(
                f"Failed to update connection activity for {connection_id}: {state_error}",
                extra={"connection_id": connection_id, "error": str(state_error)}
            )

        # Log processing metrics
        log_websocket_metrics(
            metric_type="event_processing",
            message="User action processing metrics",
            connection_id=connection_id,
            metrics={
                "processing_time_ms": processing_time_ms,
                "event_type": "oh_user_action"
            }
        )

    except Exception as e:
        processing_time_ms = (time.time() - start_time) * 1000

        error_response = WebSocketErrorResponseBuilder.create_error_response(
            WebSocketErrorCode.EVENT_PROCESSING_FAILED,
            f"Failed to process user action: {str(e)}",
            correlation_id=correlation_id,
            details={
                "exception": str(e),
                "type": type(e).__name__,
                "processing_time_ms": processing_time_ms,
                "event_data_keys": list(data.keys()) if isinstance(data, dict) else None
            }
        )

        log_websocket_error(
            error_type="event_processing",
            message=f"Failed to process user action: {str(e)}",
            connection_id=connection_id,
            error_details={
                "exception": str(e),
                "type": type(e).__name__,
                "processing_time_ms": processing_time_ms,
                "event_data_keys": list(data.keys()) if isinstance(data, dict) else None
            }
        )

        # Track error in connection state
        try:
            await connection_state_manager.increment_error_count(connection_id)
        except Exception as state_error:
            logger.debug(
                f"Failed to increment error count for {connection_id}: {state_error}",
                extra={"connection_id": connection_id, "error": str(state_error)}
            )

        await error_emitter.emit_error(connection_id, error_response)
        raise


@sio.event
async def oh_action(connection_id: str, data: dict[str, Any]) -> None:
    # TODO: Remove this handler once all clients are updated to use oh_user_action
    # Keeping for backward compatibility with in-progress sessions
    start_time = time.time()

    # Use existing correlation ID if available, or generate a new one
    correlation_id = CorrelationIdManager.get_correlation_id()
    if not correlation_id:
        correlation_id = CorrelationIdManager.generate_correlation_id()
        CorrelationIdManager.set_correlation_id(correlation_id)

    log_websocket_event(
        event_type="legacy_action_received",
        message="Received legacy action event (oh_action)",
        connection_id=connection_id,
        event_data=data,
        level="debug"
    )

    try:
        await conversation_manager.send_to_event_stream(connection_id, data)

        processing_time_ms = (time.time() - start_time) * 1000
        log_websocket_event(
            event_type="legacy_action_processed",
            message="Legacy action processed successfully",
            connection_id=connection_id,
            processing_time_ms=processing_time_ms,
            level="debug"
        )

        # Update connection activity
        try:
            await connection_state_manager.update_last_activity(connection_id)
        except Exception as state_error:
            # Don't fail the action if state update fails, just log it
            logger.debug(
                f"Failed to update connection activity for {connection_id}: {state_error}",
                extra={"connection_id": connection_id, "error": str(state_error)}
            )

        # Log processing metrics
        log_websocket_metrics(
            metric_type="event_processing",
            message="Legacy action processing metrics",
            connection_id=connection_id,
            metrics={
                "processing_time_ms": processing_time_ms,
                "event_type": "oh_action",
                "is_legacy": True
            }
        )

    except Exception as e:
        processing_time_ms = (time.time() - start_time) * 1000

        error_response = WebSocketErrorResponseBuilder.create_error_response(
            WebSocketErrorCode.EVENT_PROCESSING_FAILED,
            f"Failed to process legacy action: {str(e)}",
            correlation_id=correlation_id,
            details={
                "exception": str(e),
                "type": type(e).__name__,
                "processing_time_ms": processing_time_ms,
                "event_data_keys": list(data.keys()) if isinstance(data, dict) else None,
                "is_legacy": True
            }
        )

        log_websocket_error(
            error_type="event_processing",
            message=f"Failed to process legacy action: {str(e)}",
            connection_id=connection_id,
            error_details={
                "exception": str(e),
                "type": type(e).__name__,
                "processing_time_ms": processing_time_ms,
                "event_data_keys": list(data.keys()) if isinstance(data, dict) else None,
                "is_legacy": True
            }
        )

        # Track error in connection state
        try:
            await connection_state_manager.increment_error_count(connection_id)
        except Exception as state_error:
            logger.debug(
                f"Failed to increment error count for {connection_id}: {state_error}",
                extra={"connection_id": connection_id, "error": str(state_error)}
            )

        await error_emitter.emit_error(connection_id, error_response)
        raise


@sio.event
async def disconnect(connection_id: str) -> None:
    start_time = time.time()

    # Use existing correlation ID if available, or generate a new one
    correlation_id = CorrelationIdManager.get_correlation_id()
    if not correlation_id:
        correlation_id = CorrelationIdManager.generate_correlation_id()
        CorrelationIdManager.set_correlation_id(correlation_id)

    log_websocket_connection(
        event_type="disconnect_initiated",
        message="WebSocket disconnection initiated",
        connection_id=connection_id
    )

    try:
        await conversation_manager.disconnect_from_session(connection_id)

        # Clean up connection state
        try:
            await connection_state_manager.delete_connection_state(connection_id)
            logger.info(
                f"Cleaned up connection state for {connection_id}",
                extra={"connection_id": connection_id}
            )
        except Exception as state_error:
            # Don't fail disconnection if state cleanup fails, just log it
            logger.warning(
                f"Failed to clean up connection state for {connection_id}: {state_error}",
                extra={"connection_id": connection_id, "error": str(state_error)}
            )

        disconnect_time_ms = (time.time() - start_time) * 1000
        log_websocket_connection(
            event_type="disconnect_success",
            message="WebSocket disconnected successfully",
            connection_id=connection_id,
            disconnect_time_ms=disconnect_time_ms
        )

        # Log disconnection metrics
        log_websocket_metrics(
            metric_type="disconnection",
            message="Disconnection completed successfully",
            connection_id=connection_id,
            metrics={
                "disconnect_time_ms": disconnect_time_ms
            }
        )

    except Exception as e:
        disconnect_time_ms = (time.time() - start_time) * 1000
        log_websocket_error(
            error_type="disconnection",
            message=f"Error during disconnection: {str(e)}",
            connection_id=connection_id,
            error_details={
                "exception": str(e),
                "type": type(e).__name__,
                "disconnect_time_ms": disconnect_time_ms
            }
        )
        # Don't re-raise the exception as disconnection should be graceful


def _invalid_session_api_key(query_params: dict[str, list[Any]]):
    session_api_key = os.getenv('SESSION_API_KEY')
    if not session_api_key:
        return False
    query_api_keys = query_params['session_api_key']
    if not query_api_keys:
        return True
    return query_api_keys[0] != session_api_key
