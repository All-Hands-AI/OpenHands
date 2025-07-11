import itertools
import os
import re
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from jinja2 import Environment, FileSystemLoader
from pydantic import BaseModel, ConfigDict, Field

from openhands.core.config.llm_config import LLMConfig
from openhands.core.logger import openhands_logger as logger
from openhands.events.action import (
    ChangeAgentStateAction,
    NullAction,
)
from openhands.events.event_filter import EventFilter
from openhands.events.observation import (
    AgentStateChangedObservation,
    NullObservation,
)
from openhands.events.stream import EventStream
from openhands.integrations.provider import (
    PROVIDER_TOKEN_TYPE,
    ProviderHandler,
)
from openhands.integrations.service_types import (
    AuthenticationError,
    ProviderType,
    SuggestedTask,
)
from openhands.llm.llm import LLM
from openhands.runtime import get_runtime_cls
from openhands.runtime.runtime_status import RuntimeStatus
from openhands.server.data_models.agent_loop_info import AgentLoopInfo
from openhands.server.data_models.conversation_info import ConversationInfo
from openhands.server.data_models.conversation_info_result_set import (
    ConversationInfoResultSet,
)
from openhands.server.dependencies import get_dependencies
from openhands.server.services.conversation_service import (
    create_new_conversation,
    setup_init_convo_settings,
)
from openhands.server.session.conversation import ServerConversation
from openhands.server.shared import (
    ConversationStoreImpl,
    config,
    conversation_manager,
)
from openhands.server.types import LLMAuthenticationError, MissingSettingsError
from openhands.server.user_auth import (
    get_auth_type,
    get_provider_tokens,
    get_user_id,
    get_user_secrets,
    get_user_settings,
    get_user_settings_store,
)
from openhands.server.user_auth.user_auth import AuthType
from openhands.server.utils import get_conversation as get_conversation_object
from openhands.server.utils import get_conversation_store
from openhands.storage.conversation.conversation_store import ConversationStore
from openhands.storage.data_models.conversation_metadata import (
    ConversationMetadata,
    ConversationTrigger,
)
from openhands.storage.data_models.conversation_status import ConversationStatus
from openhands.storage.data_models.settings import Settings
from openhands.storage.data_models.user_secrets import UserSecrets
from openhands.storage.settings.settings_store import SettingsStore
from openhands.utils.async_utils import wait_all
from openhands.utils.conversation_summary import get_default_conversation_title

app = APIRouter(prefix='/api', dependencies=get_dependencies())


class InitSessionRequest(BaseModel):
    repository: str | None = None
    git_provider: ProviderType | None = None
    selected_branch: str | None = None
    initial_user_msg: str | None = None
    image_urls: list[str] | None = None
    replay_json: str | None = None
    suggested_task: SuggestedTask | None = None
    conversation_instructions: str | None = None
    # Only nested runtimes require the ability to specify a conversation id, and it could be a security risk
    if os.getenv('ALLOW_SET_CONVERSATION_ID', '0') == '1':
        conversation_id: str = Field(default_factory=lambda: uuid.uuid4().hex)

    model_config = ConfigDict(extra='forbid')


class ConversationResponse(BaseModel):
    status: str
    conversation_id: str
    message: str | None = None
    conversation_status: ConversationStatus | None = None


class ProvidersSetModel(BaseModel):
    providers_set: list[ProviderType] | None = None


@app.post('/conversations')
async def new_conversation(
    data: InitSessionRequest,
    user_id: str = Depends(get_user_id),
    provider_tokens: PROVIDER_TOKEN_TYPE = Depends(get_provider_tokens),
    user_secrets: UserSecrets = Depends(get_user_secrets),
    auth_type: AuthType | None = Depends(get_auth_type),
) -> ConversationResponse:
    """Initialize a new session or join an existing one.

    After successful initialization, the client should connect to the WebSocket
    using the returned conversation ID.
    """
    logger.info(f'initializing_new_conversation:{data}')
    repository = data.repository
    selected_branch = data.selected_branch
    initial_user_msg = data.initial_user_msg
    image_urls = data.image_urls or []
    replay_json = data.replay_json
    suggested_task = data.suggested_task
    git_provider = data.git_provider
    conversation_instructions = data.conversation_instructions

    conversation_trigger = ConversationTrigger.GUI

    if suggested_task:
        initial_user_msg = suggested_task.get_prompt_for_task()
        conversation_trigger = ConversationTrigger.SUGGESTED_TASK

    if auth_type == AuthType.BEARER:
        conversation_trigger = ConversationTrigger.REMOTE_API_KEY

    if (
        conversation_trigger == ConversationTrigger.REMOTE_API_KEY
        and not initial_user_msg
    ):
        return JSONResponse(
            content={
                'status': 'error',
                'message': 'Missing initial user message',
                'msg_id': 'CONFIGURATION$MISSING_USER_MESSAGE',
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    try:
        if repository:
            provider_handler = ProviderHandler(provider_tokens)
            # Check against git_provider, otherwise check all provider apis
            await provider_handler.verify_repo_provider(repository, git_provider)

        conversation_id = getattr(data, 'conversation_id', None) or uuid.uuid4().hex
        agent_loop_info = await create_new_conversation(
            user_id=user_id,
            git_provider_tokens=provider_tokens,
            custom_secrets=user_secrets.custom_secrets if user_secrets else None,
            selected_repository=repository,
            selected_branch=selected_branch,
            initial_user_msg=initial_user_msg,
            image_urls=image_urls,
            replay_json=replay_json,
            conversation_trigger=conversation_trigger,
            conversation_instructions=conversation_instructions,
            git_provider=git_provider,
            conversation_id=conversation_id,
        )

        return ConversationResponse(
            status='ok',
            conversation_id=conversation_id,
            conversation_status=agent_loop_info.status,
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
                'msg_id': RuntimeStatus.ERROR_LLM_AUTHENTICATION.value,
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    except AuthenticationError as e:
        return JSONResponse(
            content={
                'status': 'error',
                'message': str(e),
                'msg_id': RuntimeStatus.GIT_PROVIDER_AUTHENTICATION_ERROR.value,
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )


@app.get('/conversations')
async def search_conversations(
    page_id: str | None = None,
    limit: int = 20,
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
    connection_ids_to_conversation_ids = await conversation_manager.get_connections(
        filter_to_sids=conversation_ids
    )
    agent_loop_info = await conversation_manager.get_agent_loop_info(
        filter_to_sids=conversation_ids
    )
    agent_loop_info_by_conversation_id = {
        info.conversation_id: info for info in agent_loop_info
    }
    result = ConversationInfoResultSet(
        results=await wait_all(
            _get_conversation_info(
                conversation=conversation,
                num_connections=sum(
                    1
                    for conversation_id in connection_ids_to_conversation_ids.values()
                    if conversation_id == conversation.conversation_id
                ),
                agent_loop_info=agent_loop_info_by_conversation_id.get(
                    conversation.conversation_id
                ),
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
        num_connections = len(
            await conversation_manager.get_connections(filter_to_sids={conversation_id})
        )
        agent_loop_infos = await conversation_manager.get_agent_loop_info(
            filter_to_sids={conversation_id}
        )
        agent_loop_info = agent_loop_infos[0] if agent_loop_infos else None
        conversation_info = await _get_conversation_info(
            metadata, num_connections, agent_loop_info
        )
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


@app.get('/conversations/{conversation_id}/remember_prompt')
async def get_prompt(
    event_id: int,
    user_settings: SettingsStore = Depends(get_user_settings_store),
    conversation: ServerConversation | None = Depends(get_conversation_object),
):
    if conversation is None:
        return JSONResponse(
            status_code=404,
            content={'error': 'Conversation not found.'},
        )

    # get event stream for the conversation
    event_stream = conversation.event_stream

    # retrieve the relevant events
    stringified_events = _get_contextual_events(event_stream, event_id)

    # generate a prompt
    settings = await user_settings.load()
    if settings is None:
        # placeholder for error handling
        raise ValueError('Settings not found')

    llm_config = LLMConfig(
        model=settings.llm_model or '',
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
    )

    prompt_template = generate_prompt_template(stringified_events)
    prompt = generate_prompt(llm_config, prompt_template)

    return JSONResponse(
        {
            'status': 'success',
            'prompt': prompt,
        }
    )


def generate_prompt_template(events: str) -> str:
    env = Environment(loader=FileSystemLoader('openhands/microagent/prompts'))
    template = env.get_template('generate_remember_prompt.j2')
    return template.render(events=events)


def generate_prompt(llm_config: LLMConfig, prompt_template: str) -> str:
    llm = LLM(llm_config)
    messages = [
        {
            'role': 'system',
            'content': prompt_template,
        },
        {
            'role': 'user',
            'content': 'Please generate a prompt for the AI to update the special file based on the events provided.',
        },
    ]

    response = llm.completion(messages=messages)
    raw_prompt = response['choices'][0]['message']['content'].strip()
    prompt = re.search(r'<update_prompt>(.*?)</update_prompt>', raw_prompt, re.DOTALL)

    if prompt:
        return prompt.group(1).strip()
    else:
        raise ValueError('No valid prompt found in the response.')


async def _get_conversation_info(
    conversation: ConversationMetadata,
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
            selected_branch=conversation.selected_branch,
            git_provider=conversation.git_provider,
            status=getattr(agent_loop_info, 'status', ConversationStatus.STOPPED),
            runtime_status=getattr(agent_loop_info, 'runtime_status', None),
            num_connections=num_connections,
            url=agent_loop_info.url if agent_loop_info else None,
            session_api_key=getattr(agent_loop_info, 'session_api_key', None),
        )
    except Exception as e:
        logger.error(
            f'Error loading conversation {conversation.conversation_id}: {str(e)}',
            extra={'session_id': conversation.conversation_id},
        )
        return None


@app.post('/conversations/{conversation_id}/start')
async def start_conversation(
    conversation_id: str,
    providers_set: ProvidersSetModel,
    user_id: str = Depends(get_user_id),
    settings: Settings = Depends(get_user_settings),
    conversation_store: ConversationStore = Depends(get_conversation_store),
) -> ConversationResponse:
    """Start an agent loop for a conversation.

    This endpoint calls the conversation_manager's maybe_start_agent_loop method
    to start a conversation. If the conversation is already running, it will
    return the existing agent loop info.
    """
    logger.info(f'Starting conversation: {conversation_id}')

    try:
        # Check that the conversation exists
        try:
            await conversation_store.get_metadata(conversation_id)
        except Exception:
            return JSONResponse(
                content={
                    'status': 'error',
                    'conversation_id': conversation_id,
                },
                status_code=status.HTTP_404_NOT_FOUND,
            )

        # Set up conversation init data with provider information
        conversation_init_data = await setup_init_convo_settings(
            user_id, conversation_id, providers_set.providers_set or []
        )

        # Start the agent loop
        agent_loop_info = await conversation_manager.maybe_start_agent_loop(
            sid=conversation_id,
            settings=conversation_init_data,
            user_id=user_id,
        )

        return ConversationResponse(
            status='ok',
            conversation_id=conversation_id,
            conversation_status=agent_loop_info.status,
        )
    except Exception as e:
        logger.error(
            f'Error starting conversation {conversation_id}: {str(e)}',
            extra={'session_id': conversation_id},
        )
        return JSONResponse(
            content={
                'status': 'error',
                'conversation_id': conversation_id,
                'message': f'Failed to start conversation: {str(e)}',
            },
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@app.post('/conversations/{conversation_id}/stop')
async def stop_conversation(
    conversation_id: str,
    user_id: str = Depends(get_user_id),
) -> ConversationResponse:
    """Stop an agent loop for a conversation.

    This endpoint calls the conversation_manager's close_session method
    to stop a conversation.
    """
    logger.info(f'Stopping conversation: {conversation_id}')

    try:
        # Check if the conversation is running
        agent_loop_info = await conversation_manager.get_agent_loop_info(
            user_id=user_id, filter_to_sids={conversation_id}
        )
        conversation_status = (
            agent_loop_info[0].status if agent_loop_info else ConversationStatus.STOPPED
        )

        if conversation_status not in (
            ConversationStatus.STARTING,
            ConversationStatus.RUNNING,
        ):
            return ConversationResponse(
                status='ok',
                conversation_id=conversation_id,
                message='Conversation was not running',
                conversation_status=conversation_status,
            )

        # Stop the conversation
        await conversation_manager.close_session(conversation_id)

        return ConversationResponse(
            status='ok',
            conversation_id=conversation_id,
            message='Conversation stopped successfully',
            conversation_status=conversation_status,
        )
    except Exception as e:
        logger.error(
            f'Error stopping conversation {conversation_id}: {str(e)}',
            extra={'session_id': conversation_id},
        )
        return JSONResponse(
            content={
                'status': 'error',
                'conversation_id': conversation_id,
                'message': f'Failed to stop conversation: {str(e)}',
            },
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


def _get_contextual_events(event_stream: EventStream, event_id: int) -> str:
    # find the specified events to learn from
    # Get X events around the target event
    context_size = 4

    agent_event_filter = EventFilter(
        exclude_hidden=True,
        exclude_types=(
            NullAction,
            NullObservation,
            ChangeAgentStateAction,
            AgentStateChangedObservation,
        ),
    )  # the types of events that can be in an agent's history

    # from event_id - context_size to event_id..
    context_before = event_stream.search_events(
        start_id=event_id,
        filter=agent_event_filter,
        reverse=True,
        limit=context_size,
    )

    # from event_id to event_id + context_size + 1
    context_after = event_stream.search_events(
        start_id=event_id + 1,
        filter=agent_event_filter,
        limit=context_size + 1,
    )

    # context_before is in reverse chronological order, so convert to list and reverse it.
    ordered_context_before = list(context_before)
    ordered_context_before.reverse()

    all_events = itertools.chain(ordered_context_before, context_after)
    stringified_events = '\n'.join(str(event) for event in all_events)
    return stringified_events


class UpdateConversationRequest(BaseModel):
    """Request model for updating conversation metadata."""

    title: str = Field(
        ..., min_length=1, max_length=200, description='New conversation title'
    )

    model_config = ConfigDict(extra='forbid')


@app.patch('/conversations/{conversation_id}')
async def update_conversation(
    conversation_id: str,
    data: UpdateConversationRequest,
    user_id: str | None = Depends(get_user_id),
    conversation_store: ConversationStore = Depends(get_conversation_store),
) -> bool:
    """Update conversation metadata.

    This endpoint allows updating conversation details like title.
    Only the conversation owner can update the conversation.

    Args:
        conversation_id: The ID of the conversation to update
        data: The conversation update data (title, etc.)
        user_id: The authenticated user ID
        conversation_store: The conversation store dependency

    Returns:
        bool: True if the conversation was updated successfully

    Raises:
        HTTPException: If conversation is not found or user lacks permission
    """

    logger.info(
        f'Updating conversation {conversation_id} with title: {data.title}',
        extra={'session_id': conversation_id, 'user_id': user_id},
    )

    try:
        # Get the existing conversation metadata
        metadata = await conversation_store.get_metadata(conversation_id)

        # Validate that the user owns this conversation
        if user_id and metadata.user_id != user_id:
            logger.warning(
                f'User {user_id} attempted to update conversation {conversation_id} owned by {metadata.user_id}',
                extra={'session_id': conversation_id, 'user_id': user_id},
            )
            return JSONResponse(
                content={
                    'status': 'error',
                    'message': 'Permission denied: You can only update your own conversations',
                    'msg_id': 'AUTHORIZATION$PERMISSION_DENIED',
                },
                status_code=status.HTTP_403_FORBIDDEN,
            )

        # Update the conversation metadata
        original_title = metadata.title
        metadata.title = data.title.strip()
        metadata.last_updated_at = datetime.now(timezone.utc)

        # Save the updated metadata
        await conversation_store.save_metadata(metadata)

        # Emit a status update to connected clients about the title change
        try:
            status_update_dict = {
                'status_update': True,
                'type': 'info',
                'message': conversation_id,
                'conversation_title': metadata.title,
            }
            await conversation_manager.sio.emit(
                'oh_event',
                status_update_dict,
                to=f'room:{conversation_id}',
            )
        except Exception as e:
            logger.error(f'Error emitting title update event: {e}')
            # Don't fail the update if we can't emit the event

        logger.info(
            f'Successfully updated conversation {conversation_id} title from "{original_title}" to "{metadata.title}"',
            extra={'session_id': conversation_id, 'user_id': user_id},
        )

        return True

    except FileNotFoundError:
        logger.warning(
            f'Conversation {conversation_id} not found for update',
            extra={'session_id': conversation_id, 'user_id': user_id},
        )
        return JSONResponse(
            content={
                'status': 'error',
                'message': 'Conversation not found',
                'msg_id': 'CONVERSATION$NOT_FOUND',
            },
            status_code=status.HTTP_404_NOT_FOUND,
        )
    except Exception as e:
        logger.error(
            f'Error updating conversation {conversation_id}: {str(e)}',
            extra={'session_id': conversation_id, 'user_id': user_id},
        )
        return JSONResponse(
            content={
                'status': 'error',
                'message': f'Failed to update conversation: {str(e)}',
                'msg_id': 'CONVERSATION$UPDATE_ERROR',
            },
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
