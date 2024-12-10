import uuid

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from openhands.server.session.session_init_data import SessionInitData
from openhands.server.shared import session_manager

app = APIRouter(prefix='/api')


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
    conversation_id = uuid.uuid4().hex
    await session_manager.start_agent_loop(conversation_id, session_init_data)
    return JSONResponse(content={'status': 'ok', 'conversation_id': conversation_id})
