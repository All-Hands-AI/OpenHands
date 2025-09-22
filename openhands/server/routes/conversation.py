from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from openhands.core.logger import openhands_logger as logger
from openhands.events.event_filter import EventFilter
from openhands.events.event_store import EventStore
from openhands.events.serialization.event import event_to_dict
from openhands.memory.memory import Memory
from openhands.microagent.types import InputMetadata
from openhands.runtime.base import Runtime
from openhands.server.data_models.metrics_response import (
    ConversationMetricsResponse,
    CostResponse,
    MetricsResponse,
    ResponseLatencyResponse,
    TokenUsageResponse,
)
from openhands.server.dependencies import get_dependencies
from openhands.server.session.conversation import ServerConversation
from openhands.server.shared import conversation_manager, file_store
from openhands.server.user_auth import get_user_id
from openhands.server.utils import get_conversation, get_conversation_metadata
from openhands.storage.data_models.conversation_metadata import ConversationMetadata

app = APIRouter(
    prefix='/api/conversations/{conversation_id}', dependencies=get_dependencies()
)


@app.get('/config')
async def get_remote_runtime_config(
    conversation: ServerConversation = Depends(get_conversation),
) -> JSONResponse:
    """Retrieve the runtime configuration.

    Currently, this is the session ID and runtime ID (if available).
    """
    runtime = conversation.runtime
    runtime_id = runtime.runtime_id if hasattr(runtime, 'runtime_id') else None
    session_id = runtime.sid if hasattr(runtime, 'sid') else None
    return JSONResponse(
        content={
            'runtime_id': runtime_id,
            'session_id': session_id,
        }
    )


@app.get('/vscode-url')
async def get_vscode_url(
    conversation: ServerConversation = Depends(get_conversation),
) -> JSONResponse:
    """Get the VSCode URL.

    This endpoint allows getting the VSCode URL.

    Args:
        request (Request): The incoming FastAPI request object.

    Returns:
        JSONResponse: A JSON response indicating the success of the operation.
    """
    try:
        runtime: Runtime = conversation.runtime
        logger.debug(f'Runtime type: {type(runtime)}')
        logger.debug(f'Runtime VSCode URL: {runtime.vscode_url}')
        return JSONResponse(
            status_code=status.HTTP_200_OK, content={'vscode_url': runtime.vscode_url}
        )
    except Exception as e:
        logger.error(f'Error getting VSCode URL: {e}')
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                'vscode_url': None,
                'error': f'Error getting VSCode URL: {e}',
            },
        )


@app.get('/web-hosts')
async def get_hosts(
    conversation: ServerConversation = Depends(get_conversation),
) -> JSONResponse:
    """Get the hosts used by the runtime.

    This endpoint allows getting the hosts used by the runtime.

    Args:
        request (Request): The incoming FastAPI request object.

    Returns:
        JSONResponse: A JSON response indicating the success of the operation.
    """
    try:
        runtime: Runtime = conversation.runtime
        logger.debug(f'Runtime type: {type(runtime)}')
        logger.debug(f'Runtime hosts: {runtime.web_hosts}')
        return JSONResponse(status_code=200, content={'hosts': runtime.web_hosts})
    except Exception as e:
        logger.error(f'Error getting runtime hosts: {e}')
        return JSONResponse(
            status_code=500,
            content={
                'hosts': None,
                'error': f'Error getting runtime hosts: {e}',
            },
        )


@app.get('/events')
async def search_events(
    conversation_id: str,
    start_id: int = 0,
    end_id: int | None = None,
    reverse: bool = False,
    filter: EventFilter | None = None,
    limit: int = 20,
    metadata: ConversationMetadata = Depends(get_conversation_metadata),
    user_id: str | None = Depends(get_user_id),
):
    """Search through the event stream with filtering and pagination.

    Args:
        conversation_id: The conversation ID
        start_id: Starting ID in the event stream. Defaults to 0
        end_id: Ending ID in the event stream
        reverse: Whether to retrieve events in reverse order. Defaults to False.
        filter: Filter for events
        limit: Maximum number of events to return. Must be between 1 and 100. Defaults to 20
        metadata: Conversation metadata (injected by dependency)
        user_id: User ID (injected by dependency)

    Returns:
        dict: Dictionary containing:
            - events: List of matching events
            - has_more: Whether there are more matching events after this batch
    Raises:
        HTTPException: If conversation is not found or access is denied
        ValueError: If limit is less than 1 or greater than 100
    """
    if limit < 0 or limit > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail='Invalid limit'
        )

    # Create an event store to access the events directly
    event_store = EventStore(
        sid=conversation_id,
        file_store=file_store,
        user_id=user_id,
    )

    # Get matching events from the store
    events = list(
        event_store.search_events(
            start_id=start_id,
            end_id=end_id,
            reverse=reverse,
            filter=filter,
            limit=limit + 1,
        )
    )

    # Check if there are more events
    has_more = len(events) > limit
    if has_more:
        events = events[:limit]  # Remove the extra event

    events_json = [event_to_dict(event) for event in events]
    return {
        'events': events_json,
        'has_more': has_more,
    }


@app.post('/events')
async def add_event(
    request: Request, conversation: ServerConversation = Depends(get_conversation)
):
    data = await request.json()
    await conversation_manager.send_event_to_conversation(conversation.sid, data)
    return JSONResponse({'success': True})


class MicroagentResponse(BaseModel):
    """Response model for microagents endpoint."""

    name: str
    type: str
    content: str
    triggers: list[str] = []
    inputs: list[InputMetadata] = []
    tools: list[str] = []


@app.get('/microagents')
async def get_microagents(
    conversation: ServerConversation = Depends(get_conversation),
) -> JSONResponse:
    """Get all microagents associated with the conversation.

    This endpoint returns all repository and knowledge microagents that are loaded for the conversation.

    Returns:
        JSONResponse: A JSON response containing the list of microagents.
    """
    try:
        # Get the agent session for this conversation
        agent_session = conversation_manager.get_agent_session(conversation.sid)

        if not agent_session:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={'error': 'Agent session not found for this conversation'},
            )

        # Access the memory to get the microagents
        memory: Memory | None = agent_session.memory
        if memory is None:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    'error': 'Memory is not yet initialized for this conversation'
                },
            )

        # Prepare the response
        microagents = []

        # Add repo microagents
        for name, r_agent in memory.repo_microagents.items():
            microagents.append(
                MicroagentResponse(
                    name=name,
                    type='repo',
                    content=r_agent.content,
                    triggers=[],
                    inputs=r_agent.metadata.inputs,
                    tools=[
                        server.name
                        for server in r_agent.metadata.mcp_tools.stdio_servers
                    ]
                    if r_agent.metadata.mcp_tools
                    else [],
                )
            )

        # Add knowledge microagents
        for name, k_agent in memory.knowledge_microagents.items():
            microagents.append(
                MicroagentResponse(
                    name=name,
                    type='knowledge',
                    content=k_agent.content,
                    triggers=k_agent.triggers,
                    inputs=k_agent.metadata.inputs,
                    tools=[
                        server.name
                        for server in k_agent.metadata.mcp_tools.stdio_servers
                    ]
                    if k_agent.metadata.mcp_tools
                    else [],
                )
            )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={'microagents': [m.dict() for m in microagents]},
        )
    except Exception as e:
        logger.error(f'Error getting microagents: {e}')
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={'error': f'Error getting microagents: {e}'},
        )


def _convert_token_usage_to_response(token_usage) -> TokenUsageResponse:
    """Convert a TokenUsage object to TokenUsageResponse."""
    if not token_usage:
        return TokenUsageResponse()

    return TokenUsageResponse(
        model=getattr(token_usage, 'model', ''),
        prompt_tokens=getattr(token_usage, 'prompt_tokens', 0),
        completion_tokens=getattr(token_usage, 'completion_tokens', 0),
        cache_read_tokens=getattr(token_usage, 'cache_read_tokens', 0),
        cache_write_tokens=getattr(token_usage, 'cache_write_tokens', 0),
        context_window=getattr(token_usage, 'context_window', 0),
        per_turn_token=getattr(token_usage, 'per_turn_token', 0),
    )


def _convert_cost_to_response(cost) -> CostResponse:
    """Convert a Cost object to CostResponse."""
    return CostResponse(
        model=getattr(cost, 'model', ''),
        cost=getattr(cost, 'cost', 0.0),
        timestamp=getattr(cost, 'timestamp', 0.0),
    )


def _convert_latency_to_response(latency) -> ResponseLatencyResponse:
    """Convert a ResponseLatency object to ResponseLatencyResponse."""
    return ResponseLatencyResponse(
        model=getattr(latency, 'model', ''),
        latency=getattr(latency, 'latency', 0.0),
        response_id=getattr(latency, 'response_id', ''),
    )


def _convert_metrics_to_response(metrics) -> MetricsResponse:
    """Convert a Metrics object to MetricsResponse."""
    if not metrics:
        return MetricsResponse(
            accumulated_cost=0.0,
            accumulated_token_usage=TokenUsageResponse(),
            costs=[],
            response_latencies=[],
            token_usages=[],
        )

    return MetricsResponse(
        accumulated_cost=getattr(metrics, 'accumulated_cost', 0.0),
        max_budget_per_task=getattr(metrics, 'max_budget_per_task', None),
        accumulated_token_usage=_convert_token_usage_to_response(
            getattr(metrics, 'accumulated_token_usage', None)
        ),
        costs=[
            _convert_cost_to_response(cost) for cost in getattr(metrics, 'costs', [])
        ],
        response_latencies=[
            _convert_latency_to_response(latency)
            for latency in getattr(metrics, 'response_latencies', [])
        ],
        token_usages=[
            _convert_token_usage_to_response(usage)
            for usage in getattr(metrics, 'token_usages', [])
        ],
    )


@app.get('/stats')
async def get_conversation_stats(
    conversation_id: str,
    request: Request,
) -> ConversationMetricsResponse:
    """Get conversation statistics from stored pickle data.

    Returns metrics data from the conversation_stats pickle file.
    """
    try:
        # Get the file store from the session manager
        session_manager = request.app.state.session_manager
        file_store = (
            getattr(session_manager, 'file_store', None) if session_manager else None
        )

        if not file_store:
            raise HTTPException(status_code=500, detail='File store not available')

        # Get user_id from the conversation metadata
        conversation_store = request.app.state.conversation_store
        user_id = None
        if conversation_store:
            try:
                conversation = await conversation_store.get_conversation_metadata(
                    conversation_id
                )
                user_id = getattr(conversation, 'user_id', None)
            except Exception:
                pass  # Continue without user_id

        # Create ConversationStats to load the pickle data
        from openhands.llm.metrics import Metrics
        from openhands.server.services.conversation_stats import ConversationStats

        stats = ConversationStats(
            file_store=file_store,
            conversation_id=conversation_id,
            user_id=user_id,
        )

        # Get combined metrics from restored data
        combined_metrics = None
        service_metrics = {}

        # Check if we have any metrics data
        if stats.restored_metrics or stats.service_to_metrics:
            # Get combined metrics
            if stats.service_to_metrics:
                # If we have active service metrics, use those
                combined_metrics = _convert_metrics_to_response(
                    stats.get_combined_metrics()
                )
                for service_id, metrics in stats.service_to_metrics.items():
                    service_metrics[service_id] = _convert_metrics_to_response(metrics)
            elif stats.restored_metrics:
                # If we only have restored metrics, combine those
                total_metrics = Metrics()
                for metrics in stats.restored_metrics.values():
                    total_metrics.merge(metrics)
                combined_metrics = _convert_metrics_to_response(total_metrics)
                for service_id, metrics in stats.restored_metrics.items():
                    service_metrics[service_id] = _convert_metrics_to_response(metrics)

        return ConversationMetricsResponse(
            conversation_id=conversation_id,
            metrics=combined_metrics,
            service_metrics=service_metrics,
            has_active_session=conversation_id
            in (session_manager.sessions if session_manager else {}),
        )

    except Exception as e:
        logger.error(f'Error getting conversation stats: {e}')
        raise HTTPException(
            status_code=500, detail=f'Error getting conversation stats: {str(e)}'
        )
