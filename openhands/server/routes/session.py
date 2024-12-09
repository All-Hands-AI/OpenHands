from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from openhands.core.logger import openhands_logger as logger
from openhands.server.listen_socket import init_connection
from openhands.server.session.session_init_data import SessionInitData

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