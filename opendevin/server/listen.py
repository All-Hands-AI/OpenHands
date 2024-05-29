import uuid
import warnings

with warnings.catch_warnings():
    warnings.simplefilter('ignore')
    import litellm
from fastapi import FastAPI, Request, Response, UploadFile, WebSocket, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer
from fastapi.staticfiles import StaticFiles

import agenthub  # noqa F401 (we import this to get the agents registered)
from opendevin.controller.agent import Agent
from opendevin.core.config import config
from opendevin.core.logger import opendevin_logger as logger
from opendevin.events.action import ChangeAgentStateAction, NullAction
from opendevin.events.observation import AgentStateChangedObservation, NullObservation
from opendevin.events.serialization import event_to_dict
from opendevin.llm import bedrock
from opendevin.server.auth import get_sid_from_token, sign_token
from opendevin.server.session import session_manager

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:3001'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

security_scheme = HTTPBearer()


@app.middleware('http')
async def attach_session(request: Request, call_next):
    if request.url.path.startswith('/api/options/') or not request.url.path.startswith(
        '/api/'
    ):
        response = await call_next(request)
        return response

    if not request.headers.get('Authorization'):
        response = JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={'error': 'Missing Authorization header'},
        )
        return response

    auth_token = request.headers.get('Authorization')
    if 'Bearer' in auth_token:
        auth_token = auth_token.split('Bearer')[1].strip()

    request.state.sid = get_sid_from_token(auth_token)
    if request.state.sid == '':
        response = JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={'error': 'Invalid token'},
        )
        return response

    request.state.session = session_manager.get_session(request.state.sid)
    if request.state.session is None:
        response = JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={'error': 'Session not found'},
        )
        return response

    response = await call_next(request)
    return response


# This endpoint receives events from the client (i.e. the browser)
@app.websocket('/ws')
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for receiving events from the client (i.e., the browser).

    Once connected, you can send various actions:
    - Initialize the agent:
        ```json
        {"action": "initialize", "args": {"LLM_MODEL": "ollama/llama3", "AGENT": "CodeActAgent", "LANGUAGE": "en", "LLM_API_KEY": "ollama"}}
        ```
    - Start a new development task:
        ```json
        {"action": "start", "args": {"task": "write a bash script that prints hello"}}
        ```
    - Send a message:
        ```json
        {"action": "message", "args": {"content": "Hello, how are you?"}}
        ```
    - Write contents to a file:
        ```json
        {"action": "write", "args": {"path": "./greetings.txt", "content": "Hello, OpenDevin?"}}
        ```
    - Read the contents of a file:
        ```json
        {"action": "read", "args": {"path": "./greetings.txt"}}
        ```
    - Run a command:
        ```json
        {"action": "run", "args": {"command": "ls -l", "background": false, "thought": ""}}
        ```
    - Run an IPython command:
        ```json
        {"action": "run_ipython", "args": {"command": "print('Hello, IPython!')"}}
        ```
    - Kill a background command:
        ```json
        {"action": "kill", "args": {"id": "command_id"}}
        ```
    - Open a web page:
        ```json
        {"action": "browse", "args": {"url": "https://arxiv.org/html/2402.01030v2"}}
        ```
    - Search long-term memory:
        ```json
        {"action": "recall", "args": {"query": "past projects"}}
        ```
    - Add a task to the root_task:
        ```json
        {"action": "add_task", "args": {"task": "Implement feature X"}}
        ```
    - Update a task in the root_task:
        ```json
        {"action": "modify_task", "args": {"id": "0", "state": "in_progress", "thought": ""}}
        ```
    - Change the agent's state:
        ```json
        {"action": "change_agent_state", "args": {"state": "paused"}}
        ```
    - Finish the task:
        ```json
        {"action": "finish", "args": {}}
        ```
    """
    await websocket.accept()

    session = None
    if websocket.query_params.get('token'):
        token = websocket.query_params.get('token')
        sid = get_sid_from_token(token)

        if sid == '':
            await websocket.send_json({'error': 'Invalid token', 'error_code': 401})
            await websocket.close()
            return
    else:
        sid = str(uuid.uuid4())
        token = sign_token({'sid': sid})

    session = session_manager.add_or_restart_session(sid, websocket)
    await websocket.send_json({'token': token, 'status': 'ok'})

    latest_event_id = -1
    if websocket.query_params.get('latest_event_id'):
        latest_event_id = int(websocket.query_params.get('latest_event_id'))
    for event in session.agent_session.event_stream.get_events(
        start_id=latest_event_id + 1
    ):
        if isinstance(event, NullAction) or isinstance(event, NullObservation):
            continue
        if isinstance(event, ChangeAgentStateAction) or isinstance(
            event, AgentStateChangedObservation
        ):
            continue
        await websocket.send_json(event_to_dict(event))

    await session.loop_recv()


@app.get('/api/options/models')
async def get_litellm_models():
    """
    Get all models supported by LiteLLM.

    To get the models:
    ```sh
    curl http://localhost:3000/api/litellm-models
    ```
    """
    litellm_model_list = litellm.model_list + list(litellm.model_cost.keys())
    litellm_model_list_without_bedrock = bedrock.remove_error_modelId(
        litellm_model_list
    )
    bedrock_model_list = bedrock.list_foundation_models()
    model_list = litellm_model_list_without_bedrock + bedrock_model_list

    return list(set(model_list))


@app.get('/api/options/agents')
async def get_agents():
    """
    Get all agents supported by LiteLLM.

    To get the agents:
    ```sh
    curl http://localhost:3000/api/agents
    ```
    """
    agents = Agent.list_agents()
    return agents


@app.get('/api/list-files')
def list_files(request: Request, path: str = '/'):
    """
    List files.

    To list files:
    ```sh
    curl http://localhost:3000/api/list-files
    ```
    """
    if not request.state.session.agent_session.runtime:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={'error': 'Runtime not yet initialized'},
        )

    try:
        return request.state.session.agent_session.runtime.file_store.list(path)
    except Exception as e:
        logger.error(f'Error refreshing files: {e}', exc_info=False)
        error_msg = f'Error refreshing files: {e}'
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={'error': error_msg},
        )


@app.get('/api/select-file')
def select_file(file: str, request: Request):
    """
    Select a file.

    To select a file:
    ```sh
    curl http://localhost:3000/api/select-file?file=<file_path>
    ```
    """
    try:
        content = request.state.session.agent_session.runtime.file_store.read(file)
    except Exception as e:
        logger.error(f'Error opening file {file}: {e}', exc_info=False)
        error_msg = f'Error opening file: {e}'
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={'error': error_msg},
        )
    return {'code': content}


@app.post('/api/upload-files')
async def upload_file(request: Request, files: list[UploadFile]):
    """
    Upload files to the workspace.

    To upload files:
    ```sh
    curl -X POST -F "file=@<file_path1>" -F "file=@<file_path2>" http://localhost:3000/api/upload-files
    ```
    """
    try:
        for file in files:
            file_contents = await file.read()
            request.state.session.agent_session.runtime.file_store.write(
                file.filename, file_contents
            )
    except Exception as e:
        logger.error(f'Error saving files: {e}', exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={'error': f'Error saving file:s {e}'},
        )
    return {'message': 'Files uploaded successfully', 'file_count': len(files)}


@app.get('/api/root_task')
def get_root_task(request: Request):
    """
    Get root_task.

    To get the root_task:
    ```sh
    curl -H "Authorization: Bearer <TOKEN>" http://localhost:3000/api/root_task
    ```
    """
    controller = request.state.session.agent_session.controller
    if controller is not None:
        state = controller.get_state()
        if state:
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content=state.root_task.to_dict(),
            )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.get('/api/defaults')
async def appconfig_defaults():
    """
    Get default configurations.

    To get the default configurations:
    ```sh
    curl http://localhost:3000/api/defaults
    ```
    """
    return config.defaults_dict


app.mount('/', StaticFiles(directory='./frontend/dist', html=True), name='dist')
