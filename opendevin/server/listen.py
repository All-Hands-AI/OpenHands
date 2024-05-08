import shutil
import uuid
from pathlib import Path

import litellm
from fastapi import Depends, FastAPI, Response, UploadFile, WebSocket, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.staticfiles import StaticFiles

import agenthub  # noqa F401 (we import this to get the agents registered)
from opendevin.controller.agent import Agent
from opendevin.core import config
from opendevin.core.logger import opendevin_logger as logger
from opendevin.core.schema.config import ConfigType
from opendevin.llm import bedrock
from opendevin.runtime import files
from opendevin.server.agent import agent_manager
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
@app.websocket('/ws')
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    sid = get_sid_from_token(websocket.query_params.get('token') or '')
    if sid == '':
        logger.error('Failed to decode token')
        return
    session_manager.add_session(sid, websocket)
    agent_manager.register_agent(sid)
    await session_manager.loop_recv(sid, agent_manager.dispatch)


@app.get('/api/litellm-models')
async def get_litellm_models():
    """
    Get all models supported by LiteLLM.
    """
    litellm_model_list = litellm.model_list + list(litellm.model_cost.keys())
    litellm_model_list_without_bedrock = bedrock.remove_error_modelId(
        litellm_model_list
    )
    bedrock_model_list = bedrock.list_foundation_models()
    model_list = litellm_model_list_without_bedrock + bedrock_model_list

    return list(set(model_list))


@app.get('/api/agents')
async def get_agents():
    """
    Get all agents supported by LiteLLM.
    """
    agents = Agent.list_agents()
    return agents


@app.get('/api/auth')
async def get_token(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
):
    """
    Generate a JWT for authentication when starting a WebSocket connection. This endpoint checks if valid credentials
    are provided and uses them to get a session ID. If no valid credentials are provided, it generates a new session ID.
    """
    if credentials and credentials.credentials:
        sid = get_sid_from_token(credentials.credentials)
        if not sid:
            sid = str(uuid.uuid4())
            logger.info(
                f'Invalid or missing credentials, generating new session ID: {sid}'
            )
    else:
        sid = str(uuid.uuid4())
        logger.info(f'No credentials provided, generating new session ID: {sid}')

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

    return {'messages': data}


@app.get('/api/messages/total')
async def get_message_total(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
):
    sid = get_sid_from_token(credentials.credentials)
    return {'msg_total': message_stack.get_message_total(sid)}


@app.delete('/api/messages')
async def del_messages(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
):
    sid = get_sid_from_token(credentials.credentials)
    message_stack.del_messages(sid)
    return {'ok': True}


@app.get('/api/refresh-files')
def refresh_files():
    structure = files.get_folder_structure(
        Path(str(config.get(ConfigType.WORKSPACE_BASE)))
    )
    return structure.to_dict()


@app.get('/api/select-file')
def select_file(file: str):
    try:
        workspace_base = config.get(ConfigType.WORKSPACE_BASE)
        file_path = Path(workspace_base, file)
        # The following will check if the file is within the workspace base and throw an exception if not
        file_path.resolve().relative_to(Path(workspace_base).resolve())
        with open(file_path, 'r') as selected_file:
            content = selected_file.read()
    except Exception as e:
        logger.error(f'Error opening file {file}: {e}', exc_info=False)
        error_msg = f'Error opening file: {e}'
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={'error': error_msg},
        )
    return {'code': content}


@app.post('/api/upload-file')
async def upload_file(file: UploadFile):
    try:
        workspace_base = config.get(ConfigType.WORKSPACE_BASE)
        file_path = Path(workspace_base, file.filename)
        # The following will check if the file is within the workspace base and throw an exception if not
        file_path.resolve().relative_to(Path(workspace_base).resolve())
        with open(file_path, 'wb') as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        logger.error(f'Error saving file {file.filename}: {e}', exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={'error': f'Error saving file: {e}'},
        )
    return {'filename': file.filename, 'location': str(file_path)}


@app.get('/api/plan')
def get_plan(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
):
    sid = get_sid_from_token(credentials.credentials)
    agent = agent_manager.sid_to_agent[sid]
    controller = agent.controller
    if controller is not None:
        state = controller.get_state()
        if state:
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content=state.plan.to_dict(),
            )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.get('/')
async def docs_redirect():
    response = RedirectResponse(url='/index.html')
    return response


app.mount('/', StaticFiles(directory='./frontend/dist'), name='dist')
