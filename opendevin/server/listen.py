import uuid
from pathlib import Path
from typing import Any

import litellm
from fastapi import Depends, FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette import status
from starlette.responses import JSONResponse

import agenthub  # noqa F401 (we import this to get the agents registered)
from opendevin import config, files
from opendevin.agent import Agent
from opendevin.server.agent import AgentManager
from opendevin.server.auth import get_sid_from_token, sign_token
from opendevin.server.session import message_stack, session_manager

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:3001'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

security_scheme = HTTPBearer()


# This endpoint receives events from the client (i.e. the browser)
@app.websocket('/ws')   # type: ignore[misc]
async def websocket_endpoint(websocket: WebSocket) -> None:
    await websocket.accept()
    sid = get_sid_from_token(websocket.query_params.get('token') or '')
    if sid == '':
        return
    session_manager.add_session(sid, websocket)
    # TODO: actually the agent_manager is created for each websocket connection, even if the session id is the same,
    # we need to manage the agent in memory for reconnecting the same session id to the same agent
    agent_manager = AgentManager(sid)
    await session_manager.loop_recv(sid, agent_manager.dispatch)


@app.get('/litellm-models')   # type: ignore[misc]
async def get_litellm_models() -> list[str]:
    """
    Get all models supported by LiteLLM.
    """
    return list(set(litellm.model_list + list(litellm.model_cost.keys())))


@app.get('/litellm-agents')   # type: ignore[misc]
async def get_litellm_agents() -> list[str]:
    """
    Get all agents supported by LiteLLM.
    """
    return Agent.listAgents()


@app.get('/auth')   # type: ignore[misc]
async def get_token(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
) -> JSONResponse:
    """
    Get token for authentication when starts a websocket connection.
    """
    sid = get_sid_from_token(credentials.credentials) or str(uuid.uuid4())
    token = sign_token({'sid': sid})
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={'token': token},
    )


@app.get('/messages')   # type: ignore[misc]
async def get_messages(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
) -> JSONResponse:
    data = []
    sid = get_sid_from_token(credentials.credentials)
    if sid != '':
        data = message_stack.get_messages(sid)

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={'messages': data},
    )


@app.get('/messages/total')   # type: ignore[misc]
async def get_message_total(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
) -> JSONResponse:
    sid = get_sid_from_token(credentials.credentials)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={'msg_total': message_stack.get_message_total(sid)},
    )


@app.delete('/messages')   # type: ignore[misc]
async def del_messages(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
) -> JSONResponse:
    sid = get_sid_from_token(credentials.credentials)
    message_stack.del_messages(sid)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={'ok': True},
    )


@app.get('/configurations')   # type: ignore[misc]
def read_default_model() -> dict[str, str | int | None]:
    return config.get_all()


@app.get('/refresh-files')   # type: ignore[misc]
def refresh_files() -> dict[str, Any]:
    structure = files.get_folder_structure(
        Path(str(config.get('WORKSPACE_DIR'))))
    return structure.to_dict()


@app.get('/select-file')   # type: ignore[misc]
def select_file(file: str) -> dict[str, Any]:
    with open(Path(Path(str(config.get('WORKSPACE_DIR'))), file), 'r') as selected_file:
        content = selected_file.read()
    return {'code': content}
