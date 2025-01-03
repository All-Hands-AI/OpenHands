import uuid
from datetime import datetime
from typing import Callable

from fastapi import APIRouter, Body, Request
from fastapi.responses import JSONResponse
from github import Github
from pydantic import BaseModel

from openhands.core.logger import openhands_logger as logger
from openhands.events.stream import EventStreamSubscriber
from openhands.server.routes.settings import ConversationStoreImpl, SettingsStoreImpl
from openhands.server.session.conversation_init_data import ConversationInitData
from openhands.server.shared import config, session_manager
from openhands.storage.data_models.conversation_info import ConversationInfo
from openhands.storage.data_models.conversation_info_result_set import (
    ConversationInfoResultSet,
)
from openhands.storage.data_models.conversation_metadata import ConversationMetadata
from openhands.storage.data_models.conversation_status import ConversationStatus
from openhands.utils.async_utils import (
    GENERAL_TIMEOUT,
    call_async_from_sync,
    call_sync_from_async,
    wait_all,
)

app = APIRouter(prefix='/api')
UPDATED_AT_CALLBACK_ID = 'updated_at_callback_id'


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
    logger.info('Initializing new conversation')
    github_token = data.github_token or ''

    logger.info('Loading settings')
    settings_store = await SettingsStoreImpl.get_instance(config, github_token)
    settings = await settings_store.load()
    logger.info('Settings loaded')

    session_init_args: dict = {}
    if settings:
        session_init_args = {**settings.__dict__, **session_init_args}

    session_init_args['github_token'] = github_token
    session_init_args['selected_repository'] = data.selected_repository
    conversation_init_data = ConversationInitData(**session_init_args)
    logger.info('Loading conversation store')
    conversation_store = await ConversationStoreImpl.get_instance(config, github_token)
    logger.info('Conversation store loaded')

    conversation_id = uuid.uuid4().hex
    while await conversation_store.exists(conversation_id):
        logger.warning(f'Collision on conversation ID: {conversation_id}. Retrying...')
        conversation_id = uuid.uuid4().hex
    logger.info(f'New conversation ID: {conversation_id}')

    user_id = ''
    if data.github_token:
        logger.info('Fetching Github user ID')
        with Github(data.github_token) as g:
            gh_user = await call_sync_from_async(g.get_user)
            user_id = gh_user.id

    logger.info(f'Saving metadata for conversation {conversation_id}')
    await conversation_store.save_metadata(
        ConversationMetadata(
            conversation_id=conversation_id,
            github_user_id=user_id,
            selected_repository=data.selected_repository,
        )
    )

    logger.info(f'Starting agent loop for conversation {conversation_id}')
    event_stream = await session_manager.maybe_start_agent_loop(
        conversation_id, conversation_init_data
    )
    try:
        event_stream.subscribe(
            EventStreamSubscriber.SERVER,
            _create_conversation_update_callback(
                data.github_token or '', conversation_id
            ),
            UPDATED_AT_CALLBACK_ID,
        )
    except ValueError:
        pass  # Already subscribed - take no action
    logger.info(f'Finished initializing conversation {conversation_id}')
    return JSONResponse(content={'status': 'ok', 'conversation_id': conversation_id})


@app.get('/conversations')
async def search_conversations(
    request: Request,
    page_id: str | None = None,
    limit: int = 20,
) -> ConversationInfoResultSet:
    github_token = getattr(request.state, 'github_token', '') or ''
    conversation_store = await ConversationStoreImpl.get_instance(config, github_token)
    conversation_metadata_result_set = await conversation_store.search(page_id, limit)
    conversation_ids = set(
        conversation.conversation_id
        for conversation in conversation_metadata_result_set.results
    )
    running_conversations = await session_manager.get_agent_loop_running(
        set(conversation_ids)
    )
    result = ConversationInfoResultSet(
        results=await wait_all(
            _get_conversation_info(
                conversation=conversation,
                is_running=conversation.conversation_id in running_conversations,
            )
            for conversation in conversation_metadata_result_set.results
        ),
        next_page_id=conversation_metadata_result_set.next_page_id,
    )
    return result


@app.get('/conversations/{conversation_id}')
async def get_conversation(
    conversation_id: str, request: Request
) -> ConversationInfo | None:
    github_token = getattr(request.state, 'github_token', '') or ''
    conversation_store = await ConversationStoreImpl.get_instance(config, github_token)
    try:
        metadata = await conversation_store.get_metadata(conversation_id)
        is_running = await session_manager.is_agent_loop_running(conversation_id)
        conversation_info = await _get_conversation_info(metadata, is_running)
        return conversation_info
    except FileNotFoundError:
        return None


@app.patch('/conversations/{conversation_id}')
async def update_conversation(
    request: Request, conversation_id: str, title: str = Body(embed=True)
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


async def _get_conversation_info(
    conversation: ConversationMetadata,
    is_running: bool,
) -> ConversationInfo | None:
    try:
        title = conversation.title
        if not title:
            title = f'Conversation {conversation.conversation_id[:5]}'
        return ConversationInfo(
            conversation_id=conversation.conversation_id,
            title=title,
            last_updated_at=conversation.last_updated_at,
            selected_repository=conversation.selected_repository,
            status=ConversationStatus.RUNNING
            if is_running
            else ConversationStatus.STOPPED,
        )
    except Exception:  # type: ignore
        logger.warning(
            f'Error loading conversation: {conversation.conversation_id[:5]}',
            exc_info=True,
            stack_info=True,
        )
        return None


def _create_conversation_update_callback(
    github_token: str, conversation_id: str
) -> Callable:
    def callback(*args, **kwargs):
        call_async_from_sync(
            _update_timestamp_for_conversation,
            GENERAL_TIMEOUT,
            github_token,
            conversation_id,
        )

    return callback


async def _update_timestamp_for_conversation(github_token: str, conversation_id: str):
    conversation_store = await ConversationStoreImpl.get_instance(config, github_token)
    conversation = await conversation_store.get_metadata(conversation_id)
    conversation.last_updated_at = datetime.now()
    await conversation_store.save_metadata(conversation)
