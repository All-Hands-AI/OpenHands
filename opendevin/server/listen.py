import configparser
import os
import re
import uuid
import warnings
from pathlib import Path

from pathspec import PathSpec
from pathspec.patterns import GitWildMatchPattern

from opendevin.server.data_models.feedback import FeedbackDataModel, store_feedback

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
from opendevin.events.observation import (
    AgentStateChangedObservation,
    NullObservation,
)
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

# Determine the project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Path to the configuration file
CONFIG_FILE = PROJECT_ROOT / 'config' / 'file_uploads.conf'


def load_file_upload_config():
    """
    Load file upload configuration from the INI-style config file (optional).
    """
    if not CONFIG_FILE.exists():
        logger.info(f'Config file not found: {CONFIG_FILE}. Using default values.')
        return 0, True, {'.*'}  # Default values when file doesn't exist

    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)

    # Load general configuration
    try:
        max_file_size_mb = config.getint('config', 'max_file_size_mb', fallback=0)
        restrict_file_types = config.getboolean(
            'config', 'restrict_file_types', fallback=True
        )
    except configparser.Error as e:
        logger.error(f'Error reading [config] section in {CONFIG_FILE}: {str(e)}')
        max_file_size_mb, restrict_file_types = 0, True

    # Load allowed extensions
    allowed_extensions = set()
    try:
        if 'allowed-file-types' in config:
            for key, value in config['allowed-file-types'].items():
                if value.lower() == 'true':
                    ext = f'.{key}'
                    if re.match(r'^\.\w{1,10}$', ext) or ext == '.*' or ext == '.':
                        allowed_extensions.add(ext)
                    else:
                        logger.warning(f'Invalid extension in {CONFIG_FILE}: {ext}')
    except configparser.Error as e:
        logger.error(
            f'Error reading [allowed-file-types] section in {CONFIG_FILE}: {str(e)}'
        )

    # If no extensions are specified or restrictions are disabled, allow all
    if not restrict_file_types or not allowed_extensions:
        allowed_extensions = {'.*'}

    return max_file_size_mb, restrict_file_types, allowed_extensions


# Load configuration
MAX_FILE_SIZE_MB, RESTRICT_FILE_TYPES, ALLOWED_EXTENSIONS = load_file_upload_config()


def is_extension_allowed(filename):
    """
    Check if the file is allowed, supporting wildcards and files without extensions.
    Case-sensitive for extensions.
    """
    file_ext = os.path.splitext(filename)[1]  # Keep original case
    return (
        '.*' in ALLOWED_EXTENSIONS
        or file_ext in ALLOWED_EXTENSIONS
        or (file_ext == '' and '.' in ALLOWED_EXTENSIONS)
    )


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

    return list(sorted(set(model_list)))


@app.get('/api/options/agents')
async def get_agents():
    """
    Get all agents supported by LiteLLM.

    To get the agents:
    ```sh
    curl http://localhost:3000/api/agents
    ```
    """
    agents = sorted(Agent.list_agents())
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
        # Get the full path of the requested directory
        full_path = (
            request.state.session.agent_session.runtime.file_store.get_full_path(path)
        )

        # Check if .gitignore exists
        gitignore_path = os.path.join(full_path, '.gitignore')
        if os.path.exists(gitignore_path):
            # Use PathSpec to parse .gitignore
            with open(gitignore_path, 'r') as f:
                spec = PathSpec.from_lines(GitWildMatchPattern, f.readlines())
        else:
            # Fallback to default exclude list if .gitignore doesn't exist
            default_exclude = [
                '.git',
                '.DS_Store',
                '.svn',
                '.hg',
                '.idea',
                '.vscode',
                '.settings',
                '.pytest_cache',
                '__pycache__',
                'node_modules',
                'vendor',
                'build',
                'dist',
                'bin',
                'logs',
                'log',
                'tmp',
                'temp',
                'coverage',
                'venv',
                'env',
            ]
            spec = PathSpec.from_lines(GitWildMatchPattern, default_exclude)

        entries = request.state.session.agent_session.runtime.file_store.list(path)

        # Filter entries using PathSpec
        filtered_entries = [
            entry
            for entry in entries
            if not spec.match_file(os.path.relpath(entry, full_path))
        ]

        # Separate directories and files
        directories = []
        files = []
        for entry in filtered_entries:
            # Remove leading slash and any parent directory components
            entry_relative = entry.lstrip('/').split('/')[-1]

            # Construct the full path by joining the base path with the relative entry path
            full_entry_path = os.path.join(full_path, entry_relative)
            is_dir = os.path.isdir(full_entry_path)
            if is_dir:
                directories.append(entry)
            else:
                files.append(entry)

        # Sort directories and files separately
        directories.sort(key=str.lower)
        files.sort(key=str.lower)

        # Combine sorted directories and files
        sorted_entries = directories + files
        return sorted_entries

    except Exception as e:
        logger.error(f'Error listing files: {e}', exc_info=True)
        error_msg = f'Error listing files: {e}'
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


def sanitize_filename(filename):
    """
    Sanitize the filename to prevent directory traversal
    """
    # Remove any directory components
    filename = os.path.basename(filename)
    # Remove any non-alphanumeric characters except for .-_
    filename = re.sub(r'[^\w\-_\.]', '', filename)
    # Limit the filename length
    max_length = 255
    if len(filename) > max_length:
        name, ext = os.path.splitext(filename)
        filename = name[: max_length - len(ext)] + ext
    return filename


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
        uploaded_files = []
        for file in files:
            # Sanitize the filename
            safe_filename = sanitize_filename(file.filename)

            # Read file contents
            file_contents = await file.read()

            # Check file size (if specified)
            if MAX_FILE_SIZE_MB > 0:
                if len(file_contents) > MAX_FILE_SIZE_MB * 1024 * 1024:
                    return JSONResponse(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        content={
                            'error': f'File {safe_filename} exceeds the maximum size limit of {MAX_FILE_SIZE_MB}MB'
                        },
                    )

            # Check file type (if restriction is enabled)
            if not is_extension_allowed(safe_filename):
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={'error': f'File type not allowed for {safe_filename}'},
                )

            # Write the file
            request.state.session.agent_session.runtime.file_store.write(
                safe_filename, file_contents
            )
            uploaded_files.append(safe_filename)

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                'message': 'Files uploaded successfully',
                'uploaded_files': uploaded_files,
            },
        )
    except Exception as e:
        logger.error(f'Error saving files: {e}', exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={'error': f'Error saving files: {str(e)}'},
        )


@app.post('/api/submit-feedback')
async def submit_feedback(request: Request, feedback: FeedbackDataModel):
    """
    Upload feedback data to the feedback site.

    To upload files:
    ```sh
    curl -X POST -F "email=test@example.com" -F "token=abc" -F "feedback=positive" -F "permissions=private" -F "trajectory={}" http://localhost:3000/api/submit-feedback
    ```
    """
    # Assuming the storage service is already configured in the backend
    # and there is a function to handle the storage.
    try:
        feedback_data = store_feedback(feedback)
        return JSONResponse(status_code=200, content=feedback_data)
    except Exception as e:
        logger.error(f'Error submitting feedback: {e}')
        return JSONResponse(
            status_code=500, content={'error': 'Failed to submit feedback'}
        )


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
