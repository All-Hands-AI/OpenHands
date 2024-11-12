import asyncio
import os
import uuid
import warnings

import jwt
import requests
from dotenv import load_dotenv
from fastapi import (
    Depends,
    FastAPI,
    Request,
    WebSocket,
    status,
)
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer
from fastapi.staticfiles import StaticFiles
from pathspec import PathSpec
from pathspec.patterns import GitWildMatchPattern

with warnings.catch_warnings():
    warnings.simplefilter('ignore')
    import litellm

from openhands.security.options import SecurityAnalyzers
from openhands.server.github import (
    UserVerifier,
    authenticate_github_user,
)
from openhands.server.middleware import RateLimiter
from openhands.storage import get_file_store
from openhands.utils.async_utils import call_sync_from_async

load_dotenv()

config = load_app_config()
file_store = get_file_store(config.file_store, config.file_store_path)
session_manager = SessionManager(config, file_store)


app = FastAPI(
    dependencies=[Depends(lambda: RateLimiter(times=2, seconds=1))]
)  # Default 2 req/sec
app.add_middleware(
    LocalhostCORSMiddleware,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.add_middleware(NoCacheMiddleware)

security_scheme = HTTPBearer()


def load_file_upload_config() -> tuple[int, bool, list[str]]:
    """Load file upload configuration from the config object.

    This function retrieves the file upload settings from the global config object.
    It handles the following settings:
    - Maximum file size for uploads
    - Whether to restrict file types
    - List of allowed file extensions

    It also performs sanity checks on the values to ensure they are valid and safe.

    Returns:
        tuple: A tuple containing:
            - max_file_size_mb (int): Maximum file size in MB. 0 means no limit.
            - restrict_file_types (bool): Whether file type restrictions are enabled.
            - allowed_extensions (set): Set of allowed file extensions.
    """
    # Retrieve values from config
    max_file_size_mb = config.file_uploads_max_file_size_mb
    restrict_file_types = config.file_uploads_restrict_file_types
    allowed_extensions = config.file_uploads_allowed_extensions

    # Sanity check for max_file_size_mb
    if not isinstance(max_file_size_mb, int) or max_file_size_mb < 0:
        logger.warning(
            f'Invalid max_file_size_mb: {max_file_size_mb}. Setting to 0 (no limit).'
        )
        max_file_size_mb = 0

    # Sanity check for allowed_extensions
    if not isinstance(allowed_extensions, (list, set)) or not allowed_extensions:
        logger.warning(
            f'Invalid allowed_extensions: {allowed_extensions}. Setting to [".*"].'
        )
        allowed_extensions = ['.*']
    else:
        # Ensure all extensions start with a dot and are lowercase
        allowed_extensions = [
            ext.lower() if ext.startswith('.') else f'.{ext.lower()}'
            for ext in allowed_extensions
        ]

    # If restrictions are disabled, allow all
    if not restrict_file_types:
        allowed_extensions = ['.*']

    logger.debug(
        f'File upload config: max_size={max_file_size_mb}MB, '
        f'restrict_types={restrict_file_types}, '
        f'allowed_extensions={allowed_extensions}'
    )

    return max_file_size_mb, restrict_file_types, allowed_extensions


# Load configuration
MAX_FILE_SIZE_MB, RESTRICT_FILE_TYPES, ALLOWED_EXTENSIONS = load_file_upload_config()


def is_extension_allowed(filename):
    """Check if the file extension is allowed based on the current configuration.

    This function supports wildcards and files without extensions.
    The check is case-insensitive for extensions.

    Args:
        filename (str): The name of the file to check.

    Returns:
        bool: True if the file extension is allowed, False otherwise.
    """
    if not RESTRICT_FILE_TYPES:
        return True

    file_ext = os.path.splitext(filename)[1].lower()  # Convert to lowercase
    return (
        '.*' in ALLOWED_EXTENSIONS
        or file_ext in (ext.lower() for ext in ALLOWED_EXTENSIONS)
        or (file_ext == '' and '.' in ALLOWED_EXTENSIONS)
    )


@app.middleware('http')
async def attach_session(request: Request, call_next):
    """Middleware to attach session information to the request.

    This middleware checks for the Authorization header, validates the token,
    and attaches the corresponding session to the request state.

    Args:
        request (Request): The incoming request object.
        call_next (Callable): The next middleware or route handler in the chain.

    Returns:
        Response: The response from the next middleware or route handler.
    """
    non_authed_paths = [
        '/api/options/',
        '/api/github/callback',
        '/api/authenticate',
    ]
    if any(
        request.url.path.startswith(path) for path in non_authed_paths
    ) or not request.url.path.startswith('/api/'):
        response = await call_next(request)
        return response

    # Bypass authentication for OPTIONS requests (preflight)
    if request.method == 'OPTIONS':
        response = await call_next(request)
        return response

    user_verifier = UserVerifier()
    if user_verifier.is_active():
        signed_token = request.cookies.get('github_auth')
        if not signed_token:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={'error': 'Not authenticated'},
            )
        try:
            jwt.decode(signed_token, config.jwt_secret, algorithms=['HS256'])
        except Exception as e:
            logger.warning(f'Invalid token: {e}')
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={'error': 'Invalid token'},
            )

    if not request.headers.get('Authorization'):
        logger.warning('Missing Authorization header')
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={'error': 'Missing Authorization header'},
        )

    auth_token = request.headers.get('Authorization')
    if 'Bearer' in auth_token:
        auth_token = auth_token.split('Bearer')[1].strip()

    request.state.sid = get_sid_from_token(auth_token, config.jwt_secret)
    if request.state.sid == '':
        logger.warning('Invalid token')
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={'error': 'Invalid token'},
        )

    request.state.conversation = await session_manager.attach_to_conversation(
        request.state.sid
    )
    if request.state.conversation is None:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={'error': 'Session not found'},
        )
    try:
        response = await call_next(request)
    finally:
        await session_manager.detach_from_conversation(request.state.conversation)
    return response


@app.websocket('/ws')
@RateLimiter(times=1, seconds=5)  # 1 request per 5 seconds
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for receiving events from the client (i.e., the browser).
    Once connected, the client can send various actions:
    - Initialize the agent:
    session management, and event streaming.
        ```json
        {"action": "initialize", "args": {"LLM_MODEL": "ollama/llama3", "AGENT": "CodeActAgent", "LANGUAGE": "en", "LLM_API_KEY": "ollama"}}

    Args:
        ```
        websocket (WebSocket): The WebSocket connection object.
    - Start a new development task:
        ```json
        {"action": "start", "args": {"task": "write a bash script that prints hello"}}
        ```
    - Send a message:
        ```json
        {"action": "message", "args": {"content": "Hello, how are you?", "image_urls": ["base64_url1", "base64_url2"]}}
        ```
    - Write contents to a file:
        ```json
        {"action": "write", "args": {"path": "./greetings.txt", "content": "Hello, OpenHands?"}}
        ```
    - Read the contents of a file:
        ```json
        {"action": "read", "args": {"path": "./greetings.txt"}}
        ```
    - Run a command:
        ```json
        {"action": "run", "args": {"command": "ls -l", "thought": "", "confirmation_state": "confirmed"}}
        ```
    - Run an IPython command:
        ```json
        {"action": "run_ipython", "args": {"command": "print('Hello, IPython!')"}}
        ```
    - Open a web page:
        ```json
        {"action": "browse", "args": {"url": "https://arxiv.org/html/2402.01030v2"}}
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
    # Get protocols from Sec-WebSocket-Protocol header
    protocols = websocket.headers.get('sec-websocket-protocol', '').split(', ')

    # The first protocol should be our real protocol (e.g. 'openhands')
    # The second protocol should contain our auth token
    if len(protocols) < 3:
        logger.error('Expected 3 websocket protocols, got %d', len(protocols))
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    real_protocol = protocols[0]
    jwt_token = protocols[1] if protocols[1] != 'NO_JWT' else ''
    github_token = protocols[2] if protocols[2] != 'NO_GITHUB' else ''

    if not await authenticate_github_user(github_token):
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await asyncio.wait_for(websocket.accept(subprotocol=real_protocol), 10)

    if jwt_token:
        sid = get_sid_from_token(jwt_token, config.jwt_secret)

        if sid == '':
            await websocket.send_json({'error': 'Invalid token', 'error_code': 401})
            await websocket.close()
            return
    else:
        sid = str(uuid.uuid4())
        jwt_token = sign_token({'sid': sid}, config.jwt_secret)

    logger.info(f'New session: {sid}')
    session = session_manager.add_or_restart_session(sid, websocket)
    await websocket.send_json({'token': jwt_token, 'status': 'ok'})

    latest_event_id = -1
    if websocket.query_params.get('latest_event_id'):
        latest_event_id = int(websocket.query_params.get('latest_event_id'))

    async_stream = AsyncEventStreamWrapper(
        session.agent_session.event_stream, latest_event_id + 1
    )

    async for event in async_stream:
        if isinstance(
            event,
            (
                NullAction,
                NullObservation,
                ChangeAgentStateAction,
                AgentStateChangedObservation,
            ),
        ):
            continue
        await websocket.send_json(event_to_dict(event))

    await session.loop_recv()


@app.get('/api/options/models')
async def get_litellm_models() -> list[str]:
    """
    Get all models supported by LiteLLM.

    This function combines models from litellm and Bedrock, removing any
    error-prone Bedrock models.

    To get the models:
    ```sh
    curl http://localhost:3000/api/litellm-models
    ```

    Returns:
        list: A sorted list of unique model names.
    """
    litellm_model_list = litellm.model_list + list(litellm.model_cost.keys())
    litellm_model_list_without_bedrock = bedrock.remove_error_modelId(
        litellm_model_list
    )
    # TODO: for bedrock, this is using the default config
    llm_config: LLMConfig = config.get_llm_config()
    bedrock_model_list = []
    if (
        llm_config.aws_region_name
        and llm_config.aws_access_key_id
        and llm_config.aws_secret_access_key
    ):
        bedrock_model_list = bedrock.list_foundation_models(
            llm_config.aws_region_name,
            llm_config.aws_access_key_id,
            llm_config.aws_secret_access_key,
        )
    model_list = litellm_model_list_without_bedrock + bedrock_model_list
    for llm_config in config.llms.values():
        ollama_base_url = llm_config.ollama_base_url
        if llm_config.model.startswith('ollama'):
            if not ollama_base_url:
                ollama_base_url = llm_config.base_url
        if ollama_base_url:
            ollama_url = ollama_base_url.strip('/') + '/api/tags'
            try:
                ollama_models_list = requests.get(ollama_url, timeout=3).json()[
                    'models'
                ]
                for model in ollama_models_list:
                    model_list.append('ollama/' + model['name'])
                break
            except requests.exceptions.RequestException as e:
                logger.error(f'Error getting OLLAMA models: {e}', exc_info=True)

    return list(sorted(set(model_list)))


@app.get('/api/options/agents')
async def get_agents():
    """Get all agents supported by LiteLLM.

    To get the agents:
    ```sh
    curl http://localhost:3000/api/agents
    ```

    Returns:
        list: A sorted list of agent names.
    """
    agents = sorted(Agent.list_agents())
    return agents


@app.get('/api/options/security-analyzers')
async def get_security_analyzers():
    """Get all supported security analyzers.

    To get the security analyzers:
    ```sh
    curl http://localhost:3000/api/security-analyzers
    ```

    Returns:
        list: A sorted list of security analyzer names.
    """
    return sorted(SecurityAnalyzers.keys())


FILES_TO_IGNORE = [
    '.git/',
    '.DS_Store',
    'node_modules/',
    '__pycache__/',
]


@app.get('/api/list-files')
async def list_files(request: Request, path: str | None = None):
    """List files in the specified path.

    This function retrieves a list of files from the agent's runtime file store,
    excluding certain system and hidden files/directories.

    To list files:
    ```sh
    curl http://localhost:3000/api/list-files
    ```

    Args:
        request (Request): The incoming request object.
        path (str, optional): The path to list files from. Defaults to None.

    Returns:
        list: A list of file names in the specified path.

    Raises:
        HTTPException: If there's an error listing the files.
    """
    if not request.state.conversation.runtime:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={'error': 'Runtime not yet initialized'},
        )

    runtime: Runtime = request.state.conversation.runtime
    file_list = await call_sync_from_async(runtime.list_files, path)
    if path:
        file_list = [os.path.join(path, f) for f in file_list]

    file_list = [f for f in file_list if f not in FILES_TO_IGNORE]

    # Create a PathSpec object to match gitignore patterns
    gitignore_path = os.path.join(runtime.root_dir, '.gitignore')
    if os.path.exists(gitignore_path):
        with open(gitignore_path, 'r') as f:
            gitignore = f.read()
        spec = PathSpec.from_lines(GitWildMatchPattern, gitignore.splitlines())
        file_list = [f for f in file_list if not spec.match_file(f)]

    return file_list


@app.post('/api/authenticate')
@RateLimiter(times=1, seconds=5)  # 1 request per 5 seconds
async def authenticate(request: Request):
    token = request.headers.get('X-GitHub-Token')
    if not await authenticate_github_user(token):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={'error': 'Invalid token'},
        )

    signed_token = sign_token({'token': token}, config.jwt_secret)
    response = JSONResponse(
        status_code=status.HTTP_200_OK, content={'message': 'User authenticated'}
    )
    response.set_cookie(
        key='github_auth',
        value=signed_token,
        max_age=3600,  # 1 hour in seconds
        httponly=True,
        secure=True,
        samesite='strict',
    )
    return response


class SPAStaticFiles(StaticFiles):
    """Static files handler with rate limiting."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.limiter = RateLimiter(times=10, seconds=1)  # 10 requests per second

    async def get_response(self, path: str, scope):
        try:
            return await super().get_response(path, scope)
        except Exception:
            # FIXME: just making this HTTPException doesn't work for some reason
            return await super().get_response('index.html', scope)

    async def __call__(self, scope, receive, send) -> None:
        if scope['type'] == 'http':
            # Apply rate limiting
            await self.limiter(scope, receive, send)
        return await super().__call__(scope, receive, send)


app.mount('/', SPAStaticFiles(directory='./frontend/build', html=True), name='dist')
