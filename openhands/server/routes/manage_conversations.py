import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from openhands.core.logger import openhands_logger as logger
from openhands.events.action.message import MessageAction
from openhands.integrations.provider import (
    CUSTOM_SECRETS_TYPE_WITH_JSON_SCHEMA,
    PROVIDER_TOKEN_TYPE,
    ProviderHandler,
)
from openhands.integrations.service_types import (
    AuthenticationError,
    ProviderType,
    SuggestedTask,
)
from openhands.runtime import get_runtime_cls
from openhands.server.data_models.agent_loop_info import AgentLoopInfo
from openhands.server.data_models.conversation_info import ConversationInfo
from openhands.server.data_models.conversation_info_result_set import (
    ConversationInfoResultSet,
)
from openhands.server.session.conversation_init_data import ConversationInitData
from openhands.server.shared import (
    ConversationStoreImpl,
    SettingsStoreImpl,
    config,
    conversation_manager,
)
from openhands.server.types import LLMAuthenticationError, MissingSettingsError
from openhands.server.user_auth import (
    get_auth_type,
    get_provider_tokens,
    get_user_id,
    get_user_secrets,
)
from openhands.server.user_auth.user_auth import AuthType
from openhands.server.utils import get_conversation_store
from openhands.storage.conversation.conversation_store import ConversationStore
from openhands.storage.data_models.conversation_metadata import (
    ConversationMetadata,
    ConversationTrigger,
)
from openhands.storage.data_models.conversation_status import ConversationStatus
from openhands.storage.data_models.user_secrets import UserSecrets
from openhands.utils.async_utils import wait_all
from openhands.utils.conversation_summary import get_default_conversation_title

app = APIRouter(prefix='/api')


class InitSessionRequest(BaseModel):
    repository: str | None = None
    git_provider: ProviderType | None = None
    selected_branch: str | None = None
    initial_user_msg: str | None = None
    image_urls: list[str] | None = None
    replay_json: str | None = None
    suggested_task: SuggestedTask | None = None

    model_config = {'extra': 'forbid'}


class InitSessionResponse(BaseModel):
    status: str
    conversation_id: str
    conversation_url: str
    session_api_key: str | None
    message: str | None = None


async def _create_new_conversation(
    user_id: str | None,
    git_provider_tokens: PROVIDER_TOKEN_TYPE | None,
    custom_secrets: CUSTOM_SECRETS_TYPE_WITH_JSON_SCHEMA | None,
    selected_repository: str | None,
    selected_branch: str | None,
    initial_user_msg: str | None,
    image_urls: list[str] | None,
    replay_json: str | None,
    conversation_trigger: ConversationTrigger = ConversationTrigger.GUI,
    attach_convo_id: bool = False,
) -> AgentLoopInfo:
    logger.info(
        'Creating conversation',
        extra={
            'signal': 'create_conversation',
            'user_id': user_id,
            'trigger': conversation_trigger.value,
        },
    )
    logger.info('Loading settings')
    settings_store = await SettingsStoreImpl.get_instance(config, user_id)
    settings = await settings_store.load()
    logger.info('Settings loaded')

    session_init_args: dict[str, Any] = {}
    if settings:
        session_init_args = {**settings.__dict__, **session_init_args}
        # We could use litellm.check_valid_key for a more accurate check,
        # but that would run a tiny inference.
        if (
            not settings.llm_api_key
            or settings.llm_api_key.get_secret_value().isspace()
        ):
            logger.warning(f'Missing api key for model {settings.llm_model}')
            raise LLMAuthenticationError(
                'Error authenticating with the LLM provider. Please check your API key'
            )

    else:
        logger.warning('Settings not present, not starting conversation')
        raise MissingSettingsError('Settings not found')

    session_init_args['git_provider_tokens'] = git_provider_tokens
    session_init_args['selected_repository'] = selected_repository
    session_init_args['custom_secrets'] = custom_secrets
    session_init_args['selected_branch'] = selected_branch
    conversation_init_data = ConversationInitData(**session_init_args)
    logger.info('Loading conversation store')
    conversation_store = await ConversationStoreImpl.get_instance(config, user_id)
    logger.info('Conversation store loaded')

    conversation_id = uuid.uuid4().hex
    while await conversation_store.exists(conversation_id):
        logger.warning(f'Collision on conversation ID: {conversation_id}. Retrying...')
        conversation_id = uuid.uuid4().hex
    logger.info(
        f'New conversation ID: {conversation_id}',
        extra={'user_id': user_id, 'session_id': conversation_id},
    )

    conversation_title = get_default_conversation_title(conversation_id)

    logger.info(f'Saving metadata for conversation {conversation_id}')
    await conversation_store.save_metadata(
        ConversationMetadata(
            trigger=conversation_trigger,
            conversation_id=conversation_id,
            title=conversation_title,
            user_id=user_id,
            selected_repository=selected_repository,
            selected_branch=selected_branch,
        )
    )

    logger.info(
        f'Starting agent loop for conversation {conversation_id}',
        extra={'user_id': user_id, 'session_id': conversation_id},
    )
    initial_message_action = None
    if initial_user_msg or image_urls:
        user_msg = (
            initial_user_msg.format(conversation_id)
            if attach_convo_id and initial_user_msg
            else initial_user_msg
        )
        initial_message_action = MessageAction(
            content=user_msg or '',
            image_urls=image_urls or [],
        )
    agent_loop_info = await conversation_manager.maybe_start_agent_loop(
        conversation_id,
        conversation_init_data,
        user_id,
        initial_user_msg=initial_message_action,
        replay_json=replay_json,
    )
    logger.info(f'Finished initializing conversation {agent_loop_info.conversation_id}')
    return agent_loop_info


@app.post('/conversations')
async def new_conversation(
    data: InitSessionRequest,
    user_id: str = Depends(get_user_id),
    provider_tokens: PROVIDER_TOKEN_TYPE = Depends(get_provider_tokens),
    user_secrets: UserSecrets = Depends(get_user_secrets),
    auth_type: AuthType | None = Depends(get_auth_type),
) -> InitSessionResponse:
    """Initialize a new session or join an existing one.

    After successful initialization, the client should connect to the WebSocket
    using the returned conversation ID.
    """
    logger.info('Initializing new conversation')
    repository = data.repository
    selected_branch = data.selected_branch
    initial_user_msg = data.initial_user_msg
    image_urls = data.image_urls or []
    replay_json = data.replay_json
    suggested_task = data.suggested_task
    git_provider = data.git_provider

    conversation_trigger = ConversationTrigger.GUI

    if suggested_task:
        initial_user_msg = suggested_task.get_prompt_for_task()
        conversation_trigger = ConversationTrigger.SUGGESTED_TASK

    if auth_type == AuthType.BEARER:
        conversation_trigger = ConversationTrigger.REMOTE_API_KEY

    try:
        if repository:
            provider_handler = ProviderHandler(provider_tokens)
            # Check against git_provider, otherwise check all provider apis
            await provider_handler.verify_repo_provider(repository, git_provider)

        # Create conversation with initial message
        agent_loop_info = await _create_new_conversation(
            user_id=user_id,
            git_provider_tokens=provider_tokens,
            custom_secrets=user_secrets.custom_secrets if user_secrets else None,
            selected_repository=repository,
            selected_branch=selected_branch,
            initial_user_msg=initial_user_msg,
            image_urls=image_urls,
            replay_json=replay_json,
            conversation_trigger=conversation_trigger,
        )

        return InitSessionResponse(
            status='ok',
            conversation_id=agent_loop_info.conversation_id,
            conversation_url=agent_loop_info.url,
            session_api_key=agent_loop_info.session_api_key,
        )
    except MissingSettingsError as e:
        return JSONResponse(
            content={
                'status': 'error',
                'message': str(e),
                'msg_id': 'CONFIGURATION$SETTINGS_NOT_FOUND',
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    except LLMAuthenticationError as e:
        return JSONResponse(
            content={
                'status': 'error',
                'message': str(e),
                'msg_id': 'STATUS$ERROR_LLM_AUTHENTICATION',
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    except AuthenticationError as e:
        return JSONResponse(
            content={
                'status': 'error',
                'message': str(e),
                'msg_id': 'STATUS$GIT_PROVIDER_AUTHENTICATION_ERROR',
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )


@app.get('/conversations')
async def search_conversations(
    page_id: str | None = None,
    limit: int = 20,
    user_id: str | None = Depends(get_user_id),
    conversation_store: ConversationStore = Depends(get_conversation_store),
) -> ConversationInfoResultSet:
    conversation_metadata_result_set = await conversation_store.search(page_id, limit)

    # Filter out conversations older than max_age
    now = datetime.now(timezone.utc)
    max_age = config.conversation_max_age_seconds
    filtered_results = [
        conversation
        for conversation in conversation_metadata_result_set.results
        if hasattr(conversation, 'created_at')
        and (now - conversation.created_at.replace(tzinfo=timezone.utc)).total_seconds()
        <= max_age
    ]

    conversation_ids = set(
        conversation.conversation_id for conversation in filtered_results
    )
    running_conversations = await conversation_manager.get_running_agent_loops(
        user_id, conversation_ids
    )
    connection_ids_to_conversation_ids = await conversation_manager.get_connections(filter_to_sids=conversation_ids)
    agent_loop_info = await conversation_manager.get_agent_loop_info(filter_to_sids=conversation_ids)
    agent_loop_info_by_conversation_id = {info.conversation_id: info for info in agent_loop_info}
    result = ConversationInfoResultSet(
        results=await wait_all(
            _get_conversation_info(
                conversation=conversation,
                is_running=conversation.conversation_id in running_conversations,
                num_connections=sum(
                    1 for conversation_id in connection_ids_to_conversation_ids.values()
                    if conversation_id == conversation.conversation_id
                ),
                agent_loop_info=agent_loop_info_by_conversation_id.get(conversation.conversation_id),

            )
            for conversation in filtered_results
        ),
        next_page_id=conversation_metadata_result_set.next_page_id,
    )
    return result


@app.get('/conversations/{conversation_id}')
async def get_conversation(
    conversation_id: str,
    conversation_store: ConversationStore = Depends(get_conversation_store),
) -> ConversationInfo | None:
    try:
        metadata = await conversation_store.get_metadata(conversation_id)
        is_running = await conversation_manager.is_agent_loop_running(conversation_id)
        num_connections = len(await conversation_manager.get_connections(filter_to_sids={conversation_id}))
        agent_loop_infos = await conversation_manager.get_agent_loop_info(filter_to_sids={conversation_id})
        agent_loop_info = agent_loop_infos[0] if agent_loop_infos else None
        conversation_info = await _get_conversation_info(metadata, is_running, num_connections, agent_loop_info)
        return conversation_info
    except FileNotFoundError:
        return None


@app.delete('/conversations/{conversation_id}')
async def delete_conversation(
    conversation_id: str,
    user_id: str | None = Depends(get_user_id),
) -> bool:
    conversation_store = await ConversationStoreImpl.get_instance(config, user_id)
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
    num_connections: int,
    agent_loop_info: AgentLoopInfo | None,
) -> ConversationInfo | None:
    try:
        title = conversation.title
        if not title:
            title = get_default_conversation_title(conversation.conversation_id)
        return ConversationInfo(
            trigger=conversation.trigger,
            conversation_id=conversation.conversation_id,
            title=title,
            last_updated_at=conversation.last_updated_at,
            created_at=conversation.created_at,
            selected_repository=conversation.selected_repository,
            status=(
                ConversationStatus.RUNNING if is_running else ConversationStatus.STOPPED
            ),
            num_connections=num_connections,
            url=agent_loop_info.url if agent_loop_info else None,
            session_api_key=agent_loop_info.session_api_key if agent_loop_info else None,
        )
    except Exception as e:
        logger.error(
            f'Error loading conversation {conversation.conversation_id}: {str(e)}',
            extra={'session_id': conversation.conversation_id},
        )
        return None
