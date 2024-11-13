import asyncio
import uuid

from fastapi import FastAPI, WebSocket, status

from openhands.core.logger import openhands_logger as logger
from openhands.events.action import (
    ChangeAgentStateAction,
    NullAction,
)
from openhands.events.observation import (
    AgentStateChangedObservation,
    NullObservation,
)
from openhands.events.serialization import event_to_dict
from openhands.events.stream import AsyncEventStreamWrapper
from openhands.server.auth.auth import get_sid_from_token, sign_token
from openhands.server.github import (
    authenticate_github_user,
)
from openhands.server.shared import config, session_manager

app = FastAPI()


@app.websocket('/ws')
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
