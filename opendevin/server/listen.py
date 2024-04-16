import uuid
from pathlib import Path

import litellm
from fastapi import Depends, FastAPI, WebSocket, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.staticfiles import StaticFiles
from fastapi.responses import Response, RedirectResponse, JSONResponse

import agenthub  # noqa F401 (we import this to get the agents registered)
from opendevin import config, files
from opendevin.agent import Agent
from opendevin.logger import opendevin_logger as logger
from opendevin.server.agent import agent_manager
from opendevin.server.auth import get_sid_from_token, sign_token
from opendevin.server.session import message_stack, session_manager
from opendevin.logger import opendevin_logger as logger

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
@app.websocket('/ws')
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    sid = get_sid_from_token(websocket.query_params.get('token') or '')
    if sid == '':
        return
    session_manager.add_session(sid, websocket)
    # TODO: actually the agent_manager is created for each websocket connection, even if the session id is the same,
    # we need to manage the agent in memory for reconnecting the same session id to the same agent
    agent_manager.register_agent(sid)
    await session_manager.loop_recv(sid, agent_manager.dispatch)


@app.get('/api/litellm-models')
async def get_litellm_models():
    """
    Get all models supported by LiteLLM.
    """
    return list(set(litellm.model_list + list(litellm.model_cost.keys())))


@app.get('/api/litellm-agents')
async def get_litellm_agents():
    """
    Get all agents supported by LiteLLM.
    """
    return Agent.list_agents()


@app.get('/api/auth')
async def get_token(credentials: HTTPAuthorizationCredentials = Depends(security_scheme)):
    """
    Generate a JWT for authentication when starting a WebSocket connection. This endpoint checks if valid credentials
    are provided and uses them to get a session ID. If no valid credentials are provided, it generates a new session ID.
    """
    if credentials and credentials.credentials:
        sid = get_sid_from_token(credentials.credentials)
        if not sid:
            sid = str(uuid.uuid4())
            logger.info(f"Invalid or missing credentials, generating new session ID: {sid}")
    else:
        sid = str(uuid.uuid4())
        logger.info(f"No credentials provided, generating new session ID: {sid}")

    token = sign_token({'sid': sid})
    return {'token': token, 'status': 'ok'}


@app.get('/api/messages')
async def get_messages(
        credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
):
    data = []
    sid = get_sid_from_token(credentials.credentials)
    if sid != '':
        data = message_stack.get_messages(sid)

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={'messages': data},
    )


@app.get('/api/messages/total')
async def get_message_total(
        credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
):
    sid = get_sid_from_token(credentials.credentials)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={'msg_total': message_stack.get_message_total(sid)},
    )


@app.delete('/messages')
async def del_messages(
        credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
):
    sid = get_sid_from_token(credentials.credentials)
    message_stack.del_messages(sid)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={'ok': True},
    )


@app.get('/api/configurations')
def read_default_model():
    return config.get_fe_config()


@app.get('/api/refresh-files')
def refresh_files():
    structure = files.get_folder_structure(
        Path(str(config.get('WORKSPACE_BASE'))))
    return structure.to_dict()


@app.get('/api/select-file')
def select_file(file: str):
    try:
        workspace_base = config.get('WORKSPACE_BASE')
        file_path = Path(workspace_base, file)
        with open(file_path, 'r') as selected_file:
            content = selected_file.read()
    except Exception as e:
        logger.error(f'Error opening file {file}: {e}', exc_info=False)
        error_msg = f'Error opening file: {e}'
        return Response(f'{{"error": "{error_msg}"}}', status_code=500)
    return {'code': content}


@app.get('/')
async def docs_redirect():
    response = RedirectResponse(url='/index.html')
    return response

app.mount('/', StaticFiles(directory='./frontend/dist'), name='dist')
