import uuid
from datetime import datetime, timezone
from typing import Callable

from fastapi import APIRouter, Body, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, SecretStr

from openhands.core.logger import openhands_logger as logger
from openhands.events.action.message import MessageAction
from openhands.events.stream import EventStreamSubscriber
from openhands.integrations.github.github_service import GithubServiceImpl
from openhands.runtime import get_runtime_cls
from openhands.server.auth import get_github_token, get_user_id
from openhands.server.session.conversation_init_data import ConversationInitData
from openhands.server.shared import (
    ConversationStoreImpl,
    SettingsStoreImpl,
    config,
    conversation_manager,
)
from openhands.server.types import LLMAuthenticationError, MissingSettingsError
from openhands.storage.data_models.conversation_info import ConversationInfo
from openhands.storage.data_models.conversation_info_result_set import (
    ConversationInfoResultSet,
)
from openhands.storage.data_models.conversation_metadata import ConversationMetadata
from openhands.storage.data_models.conversation_status import ConversationStatus
from openhands.utils.async_utils import (
    GENERAL_TIMEOUT,
    call_async_from_sync,
    wait_all,
)

app = APIRouter(prefix='/api')
UPDATED_AT_CALLBACK_ID = 'updated_at_callback_id'


class InitSessionRequest(BaseModel):
    selected_repository: str | None = None
    selected_branch: str | None = None
    initial_user_msg: str | None = None
    image_urls: list[str] | None = None


async def _create_new_conversation(
    user_id: str | None,
    token: SecretStr | None,
    selected_repository: str | None,
    selected_branch: str | None,
    initial_user_msg: str | None,
    image_urls: list[str] | None,
):
    logger.info('Loading settings')
    settings_store = await SettingsStoreImpl.get_instance(config, user_id)
    settings = await settings_store.load()
    logger.info('Settings loaded')

    session_init_args: dict = {}
    if settings:
        session_init_args = {**settings.__dict__, **session_init_args}
        # We could use litellm.check_valid_key for a more accurate check,
        # but that would run a tiny inference.
        if (
            not settings.llm_api_key
            or settings.llm_api_key.get_secret_value().isspace()
        ):
            logger.warn(f'Missing api key for model {settings.llm_model}')
            raise LLMAuthenticationError(
                'Error authenticating with the LLM provider. Please check your API key'
            )

    else:
        logger.warn('Settings not present, not starting conversation')
        raise MissingSettingsError('Settings not found')

    session_init_args['github_token'] = token or SecretStr('')
    session_init_args['selected_repository'] = selected_repository
    session_init_args['selected_branch'] = selected_branch
    conversation_init_data = ConversationInitData(**session_init_args)
    logger.info('Loading conversation store')
    conversation_store = await ConversationStoreImpl.get_instance(config, user_id)
    logger.info('Conversation store loaded')

    conversation_id = uuid.uuid4().hex
    while await conversation_store.exists(conversation_id):
        logger.warning(f'Collision on conversation ID: {conversation_id}. Retrying...')
        conversation_id = uuid.uuid4().hex
    logger.info(f'New conversation ID: {conversation_id}')

    repository_title = (
        selected_repository.split('/')[-1] if selected_repository else None
    )
    conversation_title = f'{repository_title or "Conversation"} {conversation_id[:5]}'

    logger.info(f'Saving metadata for conversation {conversation_id}')
    await conversation_store.save_metadata(
        ConversationMetadata(
            conversation_id=conversation_id,
            title=conversation_title,
            github_user_id=user_id,
            selected_repository=selected_repository,
            selected_branch=selected_branch,
        )
    )

    logger.info(f'Starting agent loop for conversation {conversation_id}')
    initial_message_action = None
    if initial_user_msg or image_urls:
        initial_message_action = MessageAction(
            content=initial_user_msg or '',
            image_urls=image_urls or [],
        )
    event_stream = await conversation_manager.maybe_start_agent_loop(
        conversation_id, conversation_init_data, user_id, initial_message_action
    )
    try:
        event_stream.subscribe(
            EventStreamSubscriber.SERVER,
            _create_conversation_update_callback(user_id, conversation_id),
            UPDATED_AT_CALLBACK_ID,
        )
    except ValueError:
        pass  # Already subscribed - take no action
    logger.info(f'Finished initializing conversation {conversation_id}')

    return conversation_id


@app.post('/conversations')
async def new_conversation(request: Request, data: InitSessionRequest):
    """Initialize a new session or join an existing one.

    After successful initialization, the client should connect to the WebSocket
    using the returned conversation ID.
    """
    logger.info('Initializing new conversation')
    user_id = get_user_id(request)
    gh_client = GithubServiceImpl(user_id=user_id, token=get_github_token(request))
    github_token = await gh_client.get_latest_token()

    selected_repository = data.selected_repository
    selected_branch = data.selected_branch
    initial_user_msg = data.initial_user_msg
    image_urls = data.image_urls or []

    try:
        # Create conversation with initial message
        conversation_id = await _create_new_conversation(
            user_id,
            github_token,
            selected_repository,
            selected_branch,
            initial_user_msg,
            image_urls,
        )

        return JSONResponse(
            content={'status': 'ok', 'conversation_id': conversation_id}
        )
    except MissingSettingsError as e:
        return JSONResponse(
            content={
                'status': 'error',
                'message': str(e),
                'msg_id': 'CONFIGURATION$SETTINGS_NOT_FOUND',
            },
            status_code=400,
        )

    except LLMAuthenticationError as e:
        return JSONResponse(
            content={
                'status': 'error',
                'message': str(e),
                'msg_id': 'STATUS$ERROR_LLM_AUTHENTICATION',
            },
            status_code=400,
        )


@app.get('/conversations')
async def search_conversations(
    request: Request,
    page_id: str | None = None,
    limit: int = 20,
) -> ConversationInfoResultSet:
    conversation_store = await ConversationStoreImpl.get_instance(
        config, get_user_id(request)
    )
    conversation_metadata_result_set = await conversation_store.search(page_id, limit)
    
    # Filter out conversations older than max_age
    now = datetime.now(timezone.utc)
    max_age = config.conversation_max_age_seconds
    filtered_results = [
        conversation for conversation in conversation_metadata_result_set.results
        if hasattr(conversation, 'created_at') and 
        (now - conversation.created_at.replace(tzinfo=timezone.utc)).total_seconds() <= max_age
    ]
    
    conversation_ids = set(
        conversation.conversation_id
        for conversation in filtered_results
    )
    running_conversations = await conversation_manager.get_running_agent_loops(
        get_user_id(request), set(conversation_ids)
    )
    result = ConversationInfoResultSet(
        results=await wait_all(
            _get_conversation_info(
                conversation=conversation,
                is_running=conversation.conversation_id in running_conversations,
            )
            for conversation in filtered_results
        ),
        next_page_id=conversation_metadata_result_set.next_page_id,
    )
    return result


@app.get('/conversations/{conversation_id}')
async def get_conversation(
    conversation_id: str, request: Request
) -> ConversationInfo | None:
    conversation_store = await ConversationStoreImpl.get_instance(
        config, get_user_id(request)
    )
    try:
        metadata = await conversation_store.get_metadata(conversation_id)
        is_running = await conversation_manager.is_agent_loop_running(conversation_id)
        conversation_info = await _get_conversation_info(metadata, is_running)
        return conversation_info
    except FileNotFoundError:
        return None


@app.patch('/conversations/{conversation_id}')
async def update_conversation(
    request: Request, conversation_id: str, title: str = Body(embed=True)
) -> bool:
    conversation_store = await ConversationStoreImpl.get_instance(
        config, get_user_id(request)
    )
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
    conversation_store = await ConversationStoreImpl.get_instance(
        config, get_user_id(request)
    )
    try:
        await conversation_store.get_metadata(conversation_id)
    except FileNotFoundError:
        return False
    is_running = await conversation_manager.is_agent_loop_running(conversation_id)
    if is_running:
        await conversation_manager.close_session(conversation_id)
    runtime_cls = get_runtime_cls(config.runtime)
    await runtime_cls.delete(conversation_id)
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
            created_at=conversation.created_at,
            selected_repository=conversation.selected_repository,
            status=ConversationStatus.RUNNING
            if is_running
            else ConversationStatus.STOPPED,
        )
    except Exception as e:
        logger.error(
            f'Error loading conversation {conversation.conversation_id}: {str(e)}',
        )
        return None


def _create_conversation_update_callback(
    user_id: str | None, conversation_id: str
) -> Callable:
    def callback(*args, **kwargs):
        call_async_from_sync(
            _update_timestamp_for_conversation,
            GENERAL_TIMEOUT,
            user_id,
            conversation_id,
        )

    return callback


async def _update_timestamp_for_conversation(user_id: str, conversation_id: str):
    conversation_store = await ConversationStoreImpl.get_instance(config, user_id)
    conversation = await conversation_store.get_metadata(conversation_id)
    conversation.last_updated_at = datetime.now(timezone.utc)
    await conversation_store.save_metadata(conversation)
