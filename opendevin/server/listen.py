import shutil
import uuid
import warnings
from pathlib import Path

with warnings.catch_warnings():
    warnings.simplefilter('ignore')
    import litellm
from fastapi import Depends, FastAPI, Response, UploadFile, WebSocket, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.staticfiles import StaticFiles

import agenthub  # noqa F401 (we import this to get the agents registered)
from opendevin.controller.agent import Agent
from opendevin.core.config import config
from opendevin.core.logger import opendevin_logger as logger
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


@app.get('/api/agents')
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


@app.get('/api/auth')
async def get_token(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
):
    """
    Generate a JWT for authentication when starting a WebSocket connection. This endpoint checks if valid credentials
    are provided and uses them to get a session ID. If no valid credentials are provided, it generates a new session ID.

    To obtain an authentication token:
    ```sh
    curl -H "Authorization: Bearer 5ecRe7" http://localhost:3000/api/auth
    ```
    **Note:** If `JWT_SECRET` is set, use its value instead of `5ecRe7`.
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
    """
    Get messages.

    To get messages:
    ```sh
    curl -H "Authorization: Bearer <TOKEN>" http://localhost:3000/api/messages
    ```
    """
    data = []
    sid = get_sid_from_token(credentials.credentials)
    if sid != '':
        data = message_stack.get_messages(sid)

    return {'messages': data}


@app.get('/api/messages/total')
async def get_message_total(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
):
    """
    Get total message count.

    To get the total message count:
    ```sh
    curl -H "Authorization: Bearer <TOKEN>" http://localhost:3000/api/messages/total
    ```
    """
    sid = get_sid_from_token(credentials.credentials)
    return {'msg_total': message_stack.get_message_total(sid)}


@app.delete('/api/messages')
async def del_messages(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
):
    """
    Delete messages.

    To delete messages:
    ```sh

    curl -X DELETE -H "Authorization: Bearer <TOKEN>" http://localhost:3000/api/messages
    ```
    """
    sid = get_sid_from_token(credentials.credentials)
    message_stack.del_messages(sid)
    return {'ok': True}


@app.get('/api/refresh-files')
def refresh_files():
    """
    Refresh files.

    To refresh files:
    ```sh
    curl http://localhost:3000/api/refresh-files
    ```
    """
    structure = files.get_folder_structure(Path(str(config.workspace_base)))
    return structure.to_dict()


@app.get('/api/select-file')
def select_file(file: str):
    """
    Select a file.

    To select a file:
    ```sh
    curl http://localhost:3000/api/select-file?file=<file_path>
    ```
    """
    try:
        workspace_base = config.workspace_base
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


@app.post('/api/upload-files')
async def upload_files(files: list[UploadFile]):
    """
    Upload files to the workspace.

    To upload files:
    ```sh
    curl -X POST -F "file=@<file_path1>" -F "file=@<file_path2>" http://localhost:3000/api/upload-files
    ```
    """
    try:
        workspace_base = config.workspace_base
        for file in files:
            file_path = Path(workspace_base, file.filename)
            # The following will check if the file is within the workspace base and throw an exception if not
            file_path.resolve().relative_to(Path(workspace_base).resolve())
            with open(file_path, 'wb') as buffer:
                shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        logger.error(f'Error saving files: {e}', exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={'error': f'Error saving file:s {e}'},
        )
    return {'message': 'Files uploaded successfully', 'file_count': len(files)}


@app.get('/api/root_task')
def get_root_task(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
):
    """
    Get root_task.

    To get the root_task:
    ```sh
    curl -H "Authorization: Bearer <TOKEN>" http://localhost:3000/api/root_task
    ```
    """
    sid = get_sid_from_token(credentials.credentials)
    agent = agent_manager.sid_to_agent[sid]
    controller = agent.controller
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


@app.get('/')
async def docs_redirect():
    """
    Redirect to the API documentation.
    """
    response = RedirectResponse(url='/index.html')
    return response


app.mount('/', StaticFiles(directory='./frontend/dist'), name='dist')
