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
from openhands.core.config.mcp_config import MCPConfig
from openhands.core.logger import openhands_logger as logger
from openhands.events.action import (
    ChangeAgentStateAction,
    NullAction,
)
from openhands.events.event_filter import EventFilter
from openhands.events.event_store import EventStore
from openhands.events.observation import (
    AgentStateChangedObservation,
    NullObservation,
)
from openhands.experiments.experiment_manager import ExperimentConfig
from openhands.integrations.provider import (
    PROVIDER_TOKEN_TYPE,
    ProviderHandler,
)
from openhands.integrations.service_types import (
    CreateMicroagent,
    ProviderType,
    SuggestedTask,
)
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
    setup_init_conversation_settings,
)
from openhands.server.shared import (
    ConversationManagerImpl,
    ConversationStoreImpl,
    SettingsStoreImpl,
    config,
    conversation_manager,
    file_store,
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
from openhands.server.utils import get_conversation as get_conversation_metadata
from openhands.server.utils import get_conversation_store, validate_conversation_id
from openhands.storage.conversation.conversation_store import ConversationStore
from openhands.storage.data_models.conversation_metadata import (
    ConversationMetadata,
    ConversationTrigger,
)
from openhands.storage.data_models.conversation_status import ConversationStatus
from openhands.storage.data_models.settings import Settings
from openhands.storage.data_models.user_secrets import UserSecrets
from openhands.storage.locations import get_experiment_config_filename
from openhands.storage.settings.settings_store import SettingsStore
from openhands.utils.async_utils import wait_all
from openhands.utils.conversation_summary import get_default_conversation_title

app = APIRouter(prefix='/api', dependencies=get_dependencies())


def _filter_conversations_by_age(
    conversations: list[ConversationMetadata], max_age_seconds: int
) -> list:
    """Filter conversations by age, removing those older than max_age_seconds.

    Args:
        conversations: List of conversations to filter
        max_age_seconds: Maximum age in seconds for conversations to be included

    Returns:
        List of conversations that meet the age criteria
    """
    now = datetime.now(timezone.utc)
    filtered_results = []

    for conversation in conversations:
        # Skip conversations without created_at or older than max_age
        if not hasattr(conversation, 'created_at'):
            continue

        age_seconds = (
            now - conversation.created_at.replace(tzinfo=timezone.utc)
        ).total_seconds()
        if age_seconds > max_age_seconds:
            continue

        filtered_results.append(conversation)

    return filtered_results


async def _build_conversation_result_set(
    filtered_conversations: list, next_page_id: str | None
) -> ConversationInfoResultSet:
    """Build a ConversationInfoResultSet from filtered conversations.

    This function handles the common logic of getting conversation IDs, connections,
    agent loop info, and building the final result set.

    Args:
        filtered_conversations: List of filtered conversations
        next_page_id: Next page ID for pagination

    Returns:
        ConversationInfoResultSet with the processed conversations
    """
    conversation_ids = set(
        conversation.conversation_id for conversation in filtered_conversations
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
            for conversation in filtered_conversations
        ),
        next_page_id=next_page_id,
    )
    return result


class InitSessionRequest(BaseModel):
    repository: str | None = None
    git_provider: ProviderType | None = None
    selected_branch: str | None = None
    initial_user_msg: str | None = None
    image_urls: list[str] | None = None
    replay_json: str | None = None
    suggested_task: SuggestedTask | None = None
    create_microagent: CreateMicroagent | None = None
    conversation_instructions: str | None = None
    mcp_config: MCPConfig | None = None
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


class ResetConversationRequest(BaseModel):
    providers_set: list[ProviderType] | None = None
    delete_old_conversation: bool = False


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
    create_microagent = data.create_microagent
    git_provider = data.git_provider
    conversation_instructions = data.conversation_instructions

    conversation_trigger = ConversationTrigger.GUI

    if suggested_task:
        initial_user_msg = suggested_task.get_prompt_for_task()
        conversation_trigger = ConversationTrigger.SUGGESTED_TASK
    elif create_microagent:
        conversation_trigger = ConversationTrigger.MICROAGENT_MANAGEMENT
        # Set repository and git_provider from create_microagent if not already set
        if not repository and create_microagent.repo:
            repository = create_microagent.repo
        if not git_provider and create_microagent.git_provider:
            git_provider = create_microagent.git_provider

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
            mcp_config=data.mcp_config,
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


@app.get('/conversations')
async def search_conversations(
    page_id: str | None = None,
    limit: int = 20,
    selected_repository: str | None = None,
    conversation_trigger: ConversationTrigger | None = None,
    conversation_store: ConversationStore = Depends(get_conversation_store),
) -> ConversationInfoResultSet:
    conversation_metadata_result_set = await conversation_store.search(page_id, limit)

    # Apply age filter first using common function
    filtered_results = _filter_conversations_by_age(
        conversation_metadata_result_set.results, config.conversation_max_age_seconds
    )

    # Apply additional filters
    final_filtered_results = []
    for conversation in filtered_results:
        # Apply repository filter
        if (
            selected_repository is not None
            and conversation.selected_repository != selected_repository
        ):
            continue

        # Apply conversation trigger filter
        if (
            conversation_trigger is not None
            and conversation.trigger != conversation_trigger
        ):
            continue

        final_filtered_results.append(conversation)

    return await _build_conversation_result_set(
        final_filtered_results, conversation_metadata_result_set.next_page_id
    )


@app.get('/conversations/{conversation_id}')
async def get_conversation(
    conversation_id: str = Depends(validate_conversation_id),
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
async def delete_conversation_endpoint(
    conversation_id: str = Depends(validate_conversation_id),
    user_id: str | None = Depends(get_user_id),
) -> bool:
    """API endpoint to delete a conversation."""
    return await delete_conversation(conversation_id, user_id)


async def delete_conversation(
    conversation_id: str,
    user_id: str | None = None,
) -> bool:
    """Internal helper function to delete a conversation."""
    conversation_store = await ConversationStoreImpl.get_instance(config, user_id)
    try:
        await conversation_store.get_metadata(conversation_id)
    except FileNotFoundError:
        return False

    is_running = await conversation_manager.is_agent_loop_running(conversation_id)
    if is_running:
        await conversation_manager.close_session(conversation_id)
    try:
        runtime_cls = get_runtime_cls(config.runtime)
        await runtime_cls.delete(conversation_id)
    except Exception as e:
        logger.warning(f'Error deleting container: {str(e)}')
    await conversation_store.delete_metadata(conversation_id)
    return True


@app.get('/conversations/{conversation_id}/remember-prompt')
async def get_prompt(
    event_id: int,
    conversation_id: str = Depends(validate_conversation_id),
    user_settings: SettingsStore = Depends(get_user_settings_store),
    metadata: ConversationMetadata = Depends(get_conversation_metadata),
):
    # get event store for the conversation
    event_store = EventStore(
        sid=conversation_id, file_store=file_store, user_id=metadata.user_id
    )

    # retrieve the relevant events
    stringified_events = _get_contextual_events(event_store, event_id)

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
    prompt = generate_prompt(llm_config, prompt_template, conversation_id)

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


def generate_prompt(
    llm_config: LLMConfig, prompt_template: str, conversation_id: str
) -> str:
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

    raw_prompt = ConversationManagerImpl.request_llm_completion(
        'remember_prompt', conversation_id, llm_config, messages
    )
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
            pr_number=conversation.pr_number,
            replaced_by_conversation_id=conversation.replaced_by_conversation_id,
        )
    except Exception as e:
        logger.error(
            f'Error loading conversation {conversation.conversation_id}: {str(e)}',
            extra={'session_id': conversation.conversation_id},
        )
        return None


@app.post('/conversations/{conversation_id}/start')
async def start_conversation(
    providers_set: ProvidersSetModel,
    conversation_id: str = Depends(validate_conversation_id),
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
        conversation_init_data = await setup_init_conversation_settings(
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
    conversation_id: str = Depends(validate_conversation_id),
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


@app.post('/conversations/{conversation_id}/reset')
async def reset_conversation(
    reset_request: ResetConversationRequest,
    conversation_id: str = Depends(validate_conversation_id),
    user_id: str = Depends(get_user_id),
    settings: Settings = Depends(get_user_settings),
    conversation_store: ConversationStore = Depends(get_conversation_store),
    provider_tokens: PROVIDER_TOKEN_TYPE = Depends(get_provider_tokens),
    user_secrets: UserSecrets = Depends(get_user_secrets),
) -> ConversationResponse:
    """Reset a conversation by reusing the same Docker container/environment.

    This endpoint creates a new conversation with the same settings as the current one,
    but reuses the existing Docker container by renaming it to match the new conversation ID.
    """
    logger.info(f'Resetting conversation: {conversation_id}')

    try:
        # Get the current conversation metadata to preserve settings
        current_metadata = None
        try:
            current_metadata = await conversation_store.get_metadata(conversation_id)
        except Exception:
            current_metadata = None

        if not current_metadata:
            return JSONResponse(
                content={
                    'status': 'error',
                    'conversation_id': conversation_id,
                    'message': 'Conversation not found',
                },
                status_code=status.HTTP_404_NOT_FOUND,
            )

        # Create new conversation with preserved settings from existing conversation
        new_conversation_id = await clone_conversation(
            git_provider_tokens=provider_tokens,
            user_secrets=user_secrets,
            current_metadata=current_metadata,
        )

        container_was_reused = await rename_container(
            conversation_id, new_conversation_id
        )

        if reset_request.delete_old_conversation:
            try:
                success = await delete_conversation(conversation_id, user_id)
                if success:
                    logger.info(f'Deleted old conversation: {conversation_id}')
                else:
                    logger.info(
                        f'Conversation {conversation_id} not found, skipping deletion'
                    )
            except Exception as e:
                logger.warning(f'Error deleting old conversation: {str(e)}')
        else:
            # Update old conversation to mark it as replaced
            try:
                old_metadata = await conversation_store.get_metadata(conversation_id)
                if old_metadata:
                    old_metadata.replaced_by_conversation_id = new_conversation_id
                    await conversation_store.save_metadata(old_metadata)
                    logger.info(
                        f'Updated old conversation with replacement reference: {conversation_id} -> {new_conversation_id}'
                    )
            except FileNotFoundError:
                # Conversation doesn't exist, skip update
                logger.info(
                    f'Old conversation {conversation_id} not found, skipping update'
                )
            except Exception as e:
                logger.warning(f'Error updating old conversation title: {str(e)}')

        return ConversationResponse(
            status='ok',
            conversation_id=new_conversation_id,
            message=f'Conversation reset successfully{" with container reuse" if container_was_reused else ""}',
        )
    except Exception as e:
        logger.error(
            f'Error resetting conversation {conversation_id}: {str(e)}',
            extra={'session_id': conversation_id},
        )
        return JSONResponse(
            content={
                'status': 'error',
                'conversation_id': conversation_id,
                'message': f'Failed to reset conversation: {str(e)}',
            },
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


async def rename_container(old_conversation_id: str, new_conversation_id: str) -> bool:
    """Handle Docker container renaming when resetting a conversation.

    Args:
        old_conversation_id: The ID of the conversation being reset
        new_conversation_id: The ID of the new conversation

    Returns:
        bool: True if container was successfully reused, False otherwise
    """
    old_container_name = f'openhands-runtime-{old_conversation_id}'
    new_container_name = f'openhands-runtime-{new_conversation_id}'

    try:
        import docker

        docker_client = docker.from_env()

        # Try to get the old container
        try:
            container = docker_client.containers.get(old_container_name)

            # Stop the container first
            if container.status == 'running':
                container.stop()

            # Rename the container to match new conversation ID
            container.rename(new_container_name)
            logger.info(
                f'Renamed container from {old_container_name} to {new_container_name}'
            )

            # Update container labels and environment
            container.reload()
            return True

        except docker.errors.NotFound:
            # Container doesn't exist, will create new one
            logger.info(
                f'No existing container found for {old_container_name}, will create new one'
            )
            return False

    except Exception as e:
        logger.warning(
            f'Error handling container rename: {str(e)}, will proceed with new container'
        )
        return False


async def clone_conversation(
    git_provider_tokens: PROVIDER_TOKEN_TYPE | None,
    user_secrets: UserSecrets,
    current_metadata: ConversationMetadata,
) -> str:
    user_id = current_metadata.user_id
    settings_store = await SettingsStoreImpl.get_instance(config, user_id)
    settings = await settings_store.load()

    agent_loop_info = await create_new_conversation(
        user_id=user_id,
        git_provider_tokens=git_provider_tokens,
        custom_secrets=user_secrets.custom_secrets if user_secrets else None,
        selected_repository=current_metadata.selected_repository,
        selected_branch=current_metadata.selected_branch,
        initial_user_msg=None,
        image_urls=None,
        replay_json=None,
        conversation_instructions=None,
        conversation_trigger=current_metadata.trigger or ConversationTrigger.GUI,
        git_provider=current_metadata.git_provider,
        mcp_config=settings.mcp_config if settings else None,
    )

    # Update the conversation metadata to preserve settings that currently can't be passed to create_new_conversation()
    conversation_store = await ConversationStoreImpl.get_instance(config, user_id)
    try:
        new_metadata = await conversation_store.get_metadata(
            agent_loop_info.conversation_id
        )
        if new_metadata:
            new_metadata.title = current_metadata.title
            new_metadata.llm_model = current_metadata.llm_model
            new_metadata.pr_number = current_metadata.pr_number
            await conversation_store.save_metadata(new_metadata)
    except Exception as e:
        logger.warning(f'Failed to update conversation metadata: {str(e)}')

    return agent_loop_info.conversation_id


def _get_contextual_events(event_store: EventStore, event_id: int) -> str:
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
    context_before = event_store.search_events(
        start_id=event_id,
        filter=agent_event_filter,
        reverse=True,
        limit=context_size,
    )

    # from event_id to event_id + context_size + 1
    context_after = event_store.search_events(
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
    data: UpdateConversationRequest,
    conversation_id: str = Depends(validate_conversation_id),
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


@app.post('/conversations/{conversation_id}/exp-config')
def add_experiment_config_for_conversation(
    exp_config: ExperimentConfig,
    conversation_id: str = Depends(validate_conversation_id),
) -> bool:
    exp_config_filepath = get_experiment_config_filename(conversation_id)
    exists = False
    try:
        file_store.read(exp_config_filepath)
        exists = True
    except FileNotFoundError:
        pass

    # Don't modify again if it already exists
    if exists:
        return False

    try:
        file_store.write(exp_config_filepath, exp_config.model_dump_json())
    except Exception as e:
        logger.info(f'Failed to write experiment config for {conversation_id}: {e}')
        return True

    return False


@app.get('/microagent-management/conversations')
async def get_microagent_management_conversations(
    selected_repository: str,
    page_id: str | None = None,
    limit: int = 20,
    conversation_store: ConversationStore = Depends(get_conversation_store),
    provider_tokens: PROVIDER_TOKEN_TYPE = Depends(get_provider_tokens),
) -> ConversationInfoResultSet:
    """Get conversations for the microagent management page with pagination support.

    This endpoint returns conversations with conversation_trigger = 'microagent_management'
    and only includes conversations with active PRs. Pagination is supported.

    Args:
        page_id: Optional page ID for pagination
        limit: Maximum number of results per page (default: 20)
        selected_repository: Optional repository filter to limit results to a specific repository
        conversation_store: Conversation store dependency
        provider_tokens: Provider tokens for checking PR status
    """
    conversation_metadata_result_set = await conversation_store.search(page_id, limit)

    # Apply age filter first using common function
    filtered_results = _filter_conversations_by_age(
        conversation_metadata_result_set.results, config.conversation_max_age_seconds
    )

    # Check if the last PR is active (not closed/merged)
    provider_handler = ProviderHandler(provider_tokens)

    # Apply additional filters
    final_filtered_results = []
    for conversation in filtered_results:
        # Only include microagent_management conversations
        if conversation.trigger != ConversationTrigger.MICROAGENT_MANAGEMENT:
            continue

        # Apply repository filter if specified
        if conversation.selected_repository != selected_repository:
            continue

        if (
            conversation.pr_number
            and len(conversation.pr_number) > 0
            and conversation.selected_repository
            and conversation.git_provider
            and not await provider_handler.is_pr_open(
                conversation.selected_repository,
                conversation.pr_number[-1],  # Get the last PR number
                conversation.git_provider,
            )
        ):
            # Skip this conversation if the PR is closed/merged
            continue

        final_filtered_results.append(conversation)

    return await _build_conversation_result_set(
        final_filtered_results, conversation_metadata_result_set.next_page_id
    )
