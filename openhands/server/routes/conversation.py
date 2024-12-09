from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from openhands.core.logger import openhands_logger as logger
from openhands.runtime.base import Runtime
from openhands.server.listen_socket import init_connection
from openhands.server.middleware import AttachConversationMiddleware
from openhands.server.session.session_init_data import SessionInitData

app = APIRouter(prefix='/api')
protected_router = APIRouter(prefix='/api/conversation/{convo_id}')


class InitSessionRequest(BaseModel):
    token: str | None = None
    github_token: str | None = None
    latest_event_id: int = -1
    args: dict | None = None
    selected_repository: str | None = None


@app.post('/conversation')
async def init_session(request: Request, data: InitSessionRequest):
    """Initialize a new session or join an existing one.
    
    This endpoint replaces the WebSocket INIT event with a REST API call.
    After successful initialization, the client should connect to the WebSocket
    using the returned token.
    """
    kwargs = {k.lower(): v for k, v in (data.args or {}).items()}
    session_init_data = SessionInitData(**kwargs)
    session_init_data.github_token = data.github_token
    session_init_data.selected_repository = data.selected_repository

    # Generate a temporary connection ID for initialization
    connection_id = f"temp_{data.token or ''}"
    
    try:
        token = await init_connection(
            connection_id=connection_id,
            token=data.token,
            gh_token=data.github_token,
            session_init_data=session_init_data,
            latest_event_id=data.latest_event_id,
            return_token_only=True
        )
        return JSONResponse(content={"token": token, "status": "ok"})
    except RuntimeError as e:
        if str(e) == str(status.WS_1008_POLICY_VIOLATION):
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"error": "Authentication failed"}
            )
        raise


@protected_router.get('/config')
async def get_remote_runtime_config(request: Request):
    """Retrieve the runtime configuration.

    Currently, this is the session ID and runtime ID (if available).
    """
    runtime = request.state.conversation.runtime
    runtime_id = runtime.runtime_id if hasattr(runtime, 'runtime_id') else None
    session_id = runtime.sid if hasattr(runtime, 'sid') else None
    return JSONResponse(
        content={
            'runtime_id': runtime_id,
            'session_id': session_id,
        }
    )


@protected_router.get('/vscode-url')
async def get_vscode_url(request: Request):
    """Get the VSCode URL.

    This endpoint allows getting the VSCode URL.

    Args:
        request (Request): The incoming FastAPI request object.

    Returns:
        JSONResponse: A JSON response indicating the success of the operation.
    """
    try:
        runtime: Runtime = request.state.conversation.runtime
        logger.debug(f'Runtime type: {type(runtime)}')
        logger.debug(f'Runtime VSCode URL: {runtime.vscode_url}')
        return JSONResponse(status_code=200, content={'vscode_url': runtime.vscode_url})
    except Exception as e:
        logger.error(f'Error getting VSCode URL: {e}', exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                'vscode_url': None,
                'error': f'Error getting VSCode URL: {e}',
            },
        )


@protected_router.get('/events/search')
async def search_events(
    request: Request,
    query: str | None = None,
    start_id: int = 0,
    limit: int = 20,
    event_type: str | None = None,
    source: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
):
    """Search through the event stream with filtering and pagination.
    Args:
        request (Request): The incoming request object
        query (str, optional): Text to search for in event content
        start_id (int): Starting ID in the event stream. Defaults to 0
        limit (int): Maximum number of events to return. Must be between 1 and 100. Defaults to 20
        event_type (str, optional): Filter by event type (e.g., "FileReadAction")
        source (str, optional): Filter by event source
        start_date (str, optional): Filter events after this date (ISO format)
        end_date (str, optional): Filter events before this date (ISO format)
    Returns:
        dict: Dictionary containing:
            - events: List of matching events
            - has_more: Whether there are more matching events after this batch
    Raises:
        HTTPException: If conversation is not found
        ValueError: If limit is less than 1 or greater than 100
    """
    if not request.state.conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Conversation not found'
        )
    # Get matching events from the stream
    event_stream = request.state.conversation.event_stream
    matching_events = event_stream.get_matching_events(
        query=query,
        event_type=event_type,
        source=source,
        start_date=start_date,
        end_date=end_date,
        start_id=start_id,
        limit=limit + 1,  # Get one extra to check if there are more
    )
    # Check if there are more events
    has_more = len(matching_events) > limit
    if has_more:
        matching_events = matching_events[:limit]  # Remove the extra event
    return {
        'events': matching_events,
        'has_more': has_more,
    }

# Include the protected router and apply the middleware
app.include_router(protected_router)
app.middleware('http')(AttachConversationMiddleware(app, protected_router))
