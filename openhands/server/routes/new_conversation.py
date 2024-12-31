import json
import uuid
from datetime import datetime

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from github import Github
from pydantic import BaseModel

from openhands.core.logger import openhands_logger as logger
from openhands.server.data_models.conversation_info import ConversationInfo
from openhands.server.data_models.conversation_metadata import ConversationMetadata
from openhands.server.data_models.conversation_result_set import ConversationResultSet
from openhands.server.data_models.conversation_status import ConversationStatus
from openhands.server.routes.settings import ConversationStoreImpl, SettingsStoreImpl
from openhands.server.session.conversation_init_data import ConversationInitData
from openhands.server.shared import config, session_manager
from openhands.storage.files import FileStore
from openhands.storage.locations import get_conversation_events_dir
from openhands.utils.async_utils import call_sync_from_async
from openhands.utils.search_utils import offset_to_page_id, page_id_to_offset

app = APIRouter(prefix='/api')


class InitSessionRequest(BaseModel):
    github_token: str | None = None
    latest_event_id: int = -1
    selected_repository: str | None = None
    args: dict | None = None


@app.post('/conversations')
async def new_conversation(request: Request, data: InitSessionRequest):
    """Initialize a new session or join an existing one.
    After successful initialization, the client should connect to the WebSocket
    using the returned conversation ID
    """
    github_token = data.github_token or ''
    settings_store = await SettingsStoreImpl.get_instance(config, github_token)
    settings = await settings_store.load()

    session_init_args: dict = {}
    if settings:
        session_init_args = {**settings.__dict__, **session_init_args}

    session_init_args['github_token'] = github_token
    session_init_args['selected_repository'] = data.selected_repository
    conversation_init_data = ConversationInitData(**session_init_args)

    conversation_store = await ConversationStoreImpl.get_instance(config, github_token)

    conversation_id = uuid.uuid4().hex
    while await conversation_store.exists(conversation_id):
        logger.warning(f'Collision on conversation ID: {conversation_id}. Retrying...')
        conversation_id = uuid.uuid4().hex

    user_id = ''
    if data.github_token:
        g = Github(data.github_token)
        gh_user = await call_sync_from_async(g.get_user)
        user_id = gh_user.id

    await conversation_store.save_metadata(
        ConversationMetadata(
            conversation_id=conversation_id,
            github_user_id=user_id,
            selected_repository=data.selected_repository,
        )
    )

    await session_manager.maybe_start_agent_loop(
        conversation_id, conversation_init_data
    )
    return JSONResponse(content={'status': 'ok', 'conversation_id': conversation_id})


@app.get('/conversations')
async def search_conversations(
    request: Request,
    page_id: str | None = None,
    limit: int = 20,
) -> ConversationResultSet:
    file_store = session_manager.file_store
    conversations = []
    session_ids = [
        path.split('/')[1]
        for path in file_store.list('sessions/')
        if not path.startswith('sessions/.')
    ]
    num_sessions = len(session_ids)
    start = page_id_to_offset(page_id)
    end = min(limit + start, num_sessions)
    session_ids = session_ids[start:end]
    next_page_id = offset_to_page_id(end, end < num_sessions)
    running_sessions = await session_manager.get_agent_loop_running(set(session_ids))
    for session_id in session_ids:
        is_running = session_id in running_sessions
        conversation_info = await _get_conversation_info(
            session_id, is_running, file_store, request
        )
        if conversation_info:
            conversations.append(conversation_info)
    return ConversationResultSet(results=conversations, next_page_id=next_page_id)


async def _get_conversation_info(
    session_id: str,
    is_running: bool,
    file_store: FileStore,
    request: Request,
) -> ConversationInfo | None:
    try:
        github_token = getattr(request.state, 'github_token', '') or ''
        conversation_store = await ConversationStoreImpl.get_instance(
            config, github_token
        )
        metadata = await conversation_store.get_metadata(session_id)
        events_dir = get_conversation_events_dir(session_id)
        events = file_store.list(events_dir)
        events = sorted(events)
        event_path = events[-1]
        event = json.loads(file_store.read(event_path))
        return ConversationInfo(
            id=session_id,
            title=metadata.title,
            last_updated_at=datetime.fromisoformat(event.get('timestamp')),
            selected_repository=metadata.selected_repository,
            status=ConversationStatus.RUNNING
            if is_running
            else ConversationStatus.STOPPED,
        )
    except Exception:  # type: ignore
        logger.warning(
            f'Error loading conversation: {session_id}',
            exc_info=True,
            stack_info=True,
        )
        return None


@app.get('/conversations/{conversation_id}')
async def get_conversation(conversation_id: str, request: Request) -> ConversationInfo | None:
    file_store = session_manager.file_store
    is_running = await session_manager.is_agent_loop_running(conversation_id)
    conversation_info = await _get_conversation_info(
        conversation_id, is_running, file_store, request
    )
    return conversation_info


@app.post('/conversations/{conversation_id}')
async def update_conversation(
    conversation_id: str, title: str, request: Request
) -> bool:
    github_token = getattr(request.state, 'github_token', '') or ''
    conversation_store = await ConversationStoreImpl.get_instance(config, github_token)
    metadata = await conversation_store.get_metadata(conversation_id)
    if not metadata:
        return False
    metadata.title = title
    await conversation_store.save_metadata(metadata)
    return True


@app.delete('/conversations/{conversation_id}')
async def delete_conversation(
    conversation_id: str,
    request: Request,
) -> bool:
    github_token = getattr(request.state, 'github_token', '') or ''
    conversation_store = await ConversationStoreImpl.get_instance(config, github_token)
    try:
        await conversation_store.get_metadata(conversation_id)
    except FileNotFoundError:
        return False
    is_running = await session_manager.is_agent_loop_running(conversation_id)
    if is_running:
        return False
    await conversation_store.delete_metadata(conversation_id)
    return True
