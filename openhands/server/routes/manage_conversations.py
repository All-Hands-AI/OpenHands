import os
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import (
    APIRouter,
    Body,
    Form,
    HTTPException,
    Request,
    UploadFile,
    status,
)
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from openhands.core.logger import openhands_logger as logger
from openhands.core.schema.research import ResearchMode
from openhands.events.action.message import MessageAction
from openhands.integrations.provider import (
    PROVIDER_TOKEN_TYPE,
)
from openhands.integrations.service_types import Repository
from openhands.server.auth import (
    get_github_user_id,
    get_provider_tokens,
    get_user_id,
)
from openhands.server.data_models.conversation_info import ConversationInfo
from openhands.server.data_models.conversation_info_result_set import (
    ConversationInfoResultSet,
)
from openhands.server.modules import conversation_module
from openhands.server.session.conversation_init_data import ConversationInitData
from openhands.server.shared import (
    ConversationStoreImpl,
    config,
    conversation_manager,
    s3_handler,
)
from openhands.server.thesis_auth import (
    change_thread_visibility,
    create_thread,
    delete_thread,
    get_system_prompt_by_space_id_from_thesis_auth_server,
    get_thread_by_id,
    space_get_config_section,
)
from openhands.server.types import LLMAuthenticationError, MissingSettingsError
from openhands.storage.data_models.conversation_metadata import ConversationMetadata
from openhands.storage.data_models.conversation_status import ConversationStatus
from openhands.utils.async_utils import wait_all
from openhands.utils.conversation_summary import get_default_conversation_title
from openhands.utils.get_user_setting import get_user_setting

app = APIRouter(prefix='/api')


class InitSessionRequest(BaseModel):
    selected_repository: Repository | None = None
    selected_branch: str | None = None
    initial_user_msg: str | None = None
    image_urls: list[str] | None = None
    replay_json: str | None = None
    system_prompt: str | None = None
    user_prompt: str | None = None
    mcp_disable: dict[str, bool] | None = None
    research_mode: str | None = None
    space_id: int | None = None
    thread_follow_up: int | None = None
    followup_discover_id: str | None = None
    space_section_id: int | None = None


class ChangeVisibilityRequest(BaseModel):
    is_published: bool
    hidden_prompt: bool


class ConversationVisibility(BaseModel):
    is_published: bool
    hidden_prompt: bool


async def _create_new_conversation(
    user_id: str | None,
    git_provider_tokens: PROVIDER_TOKEN_TYPE | None,
    selected_repository: Repository | None,
    selected_branch: str | None,
    initial_user_msg: str | None,
    image_urls: list[str] | None,
    replay_json: str | None,
    system_prompt: str | None = None,
    user_prompt: str | None = None,
    attach_convo_id: bool = False,
    mnemonic: str | None = None,
    mcp_disable: dict[str, bool] | None = None,
    research_mode: str | None = None,
    knowledge_base: list[dict] | None = None,
    space_id: int | None = None,
    thread_follow_up: int | None = None,
    raw_followup_conversation_id: str | None = None,
    space_section_id: int | None = None,
    output_config: dict | None = None,
):
    logger.info(
        'Creating conversation',
        extra={'signal': 'create_conversation', 'user_id': user_id},
    )

    running_conversations = await conversation_manager.get_running_agent_loops(user_id)
    if (
        len(running_conversations) >= config.max_concurrent_conversations
        and os.getenv('RUN_MODE') == 'PROD'
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'You have reached the maximum limit of {config.max_concurrent_conversations} concurrent conversations.',
        )

    logger.info('Loading settings')
    settings = await get_user_setting(user_id)

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

    session_init_args['git_provider_tokens'] = git_provider_tokens
    session_init_args['selected_repository'] = selected_repository
    session_init_args['selected_branch'] = selected_branch
    conversation_init_data = ConversationInitData(**session_init_args)
    logger.info('Loading conversation store')
    conversation_store = await ConversationStoreImpl.get_instance(config, user_id, None)
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
            conversation_id=conversation_id,
            title=conversation_title,
            user_id=user_id,
            github_user_id=None,
            selected_repository=(
                selected_repository.full_name
                if selected_repository
                else selected_repository
            ),
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
            mode=research_mode,
        )

    await conversation_manager.maybe_start_agent_loop(
        conversation_id,
        conversation_init_data,
        user_id,
        initial_user_msg=initial_message_action,
        replay_json=replay_json,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        github_user_id=None,
        mnemonic=mnemonic,
        mcp_disable=mcp_disable,
        knowledge_base=knowledge_base,
        space_id=space_id,
        thread_follow_up=thread_follow_up,
        research_mode=research_mode,
        raw_followup_conversation_id=raw_followup_conversation_id,
        space_section_id=space_section_id,
        output_config=output_config,
    )
    logger.info(f'Finished initializing conversation {conversation_id}')

    return conversation_id, conversation_title


@app.post('/conversations')
async def new_conversation(request: Request, data: InitSessionRequest):
    """Initialize a new session or join an existing one.

    After successful initialization, the client should connect to the WebSocket
    using the returned conversation ID.
    """
    logger.info('Initializing new conversation')
    provider_tokens = get_provider_tokens(request)
    selected_repository = data.selected_repository
    selected_branch = data.selected_branch
    initial_user_msg = data.initial_user_msg
    image_urls = data.image_urls or []
    replay_json = data.replay_json
    system_prompt = data.system_prompt
    user_prompt = data.user_prompt
    user_id = get_user_id(request)
    mnemonic = request.state.user.mnemonic
    space_id = data.space_id
    thread_follow_up = data.thread_follow_up
    bearer_token = request.headers.get('Authorization')
    x_device_id = request.headers.get('x-device-id')
    followup_discover_id = data.followup_discover_id
    space_section_id = data.space_section_id
    mcp_disable = data.mcp_disable
    output_config: dict | None = None

    if space_id is not None:
        # get system prompt from thesis auth server
        system_prompt = await get_system_prompt_by_space_id_from_thesis_auth_server(
            int(space_id), bearer_token, x_device_id
        )

    try:
        knowledge_base = None
        raw_followup_conversation_id = None
        if space_section_id:
            section_config = await space_get_config_section(space_section_id)
            if section_config:
                # if initial_user_msg is None:
                #     initial_user_msg = section_config['chartPrompt']
                # else:
                #     initial_user_msg = (
                #         initial_user_msg + '\n\n' + section_config['chartPrompt']
                #     )
                mcp_disable = section_config['mcpDisable']
                if 'chartPrompt' in section_config:
                    output_config = {
                        'prompt': section_config['chartPrompt'],
                        'output': section_config['outputConfig'],
                    }

        # if space_id or thread_follow_up:
        #     knowledge_base = await search_knowledge(
        #         initial_user_msg, space_id, thread_follow_up, user_id
        # )
        # if knowledge and knowledge['data']['summary']:
        #     initial_user_msg = (
        #         f"Reference information:\n{knowledge['data']['summary']}\n\n"
        #         f"Question:\n{initial_user_msg}"
        #     )
        if thread_follow_up:
            threadData = await get_thread_by_id(thread_follow_up)
            if threadData:
                raw_followup_conversation_id = threadData['conversationId']
        start_time = time.time()
        conversation_id, conversation_title = await _create_new_conversation(
            user_id,
            provider_tokens,
            selected_repository,
            selected_branch,
            initial_user_msg,
            image_urls,
            replay_json,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            mnemonic=mnemonic,
            mcp_disable=mcp_disable,
            research_mode=data.research_mode,
            knowledge_base=knowledge_base,
            space_id=space_id,
            thread_follow_up=thread_follow_up,
            raw_followup_conversation_id=raw_followup_conversation_id,
            space_section_id=space_section_id,
            output_config=output_config,
        )

        end_time = time.time()
        logger.info(
            f'Time taken to create new conversation: {end_time - start_time} seconds'
        )
        if conversation_id and user_id is not None:
            start_time = time.time()
            await create_thread(
                space_id,
                thread_follow_up,
                conversation_id,
                data.initial_user_msg,
                bearer_token,
                x_device_id,
                followup_discover_id,
                data.research_mode,
                space_section_id,
            )
            end_time = time.time()
            logger.info(f'Time taken to create thread: {end_time - start_time} seconds')
            metadata: dict[str, Any] = {}
            metadata['hidden_prompt'] = True
            if space_id is not None:
                metadata['space_id'] = space_id
            if thread_follow_up is not None:
                metadata['thread_follow_up'] = thread_follow_up
            if raw_followup_conversation_id is not None:
                metadata['raw_followup_conversation_id'] = raw_followup_conversation_id
            if data.research_mode and data.research_mode == ResearchMode.FOLLOW_UP:
                metadata['research_mode'] = ResearchMode.FOLLOW_UP
            if data.space_section_id:
                metadata['space_section_id'] = data.space_section_id
            start_time = time.time()
            await conversation_module._update_conversation_visibility(
                conversation_id,
                False,
                user_id,
                metadata,
                conversation_title,
                'available',
            )
            end_time = time.time()
            logger.info(
                f'Time taken to update conversation visibility: {end_time - start_time} seconds'
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

    except Exception as e:
        return JSONResponse(
            content={
                'status': 'error',
                'detail': str(e.detail) if hasattr(e, 'detail') else str(e),
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )


@app.get('/conversations')
async def search_conversations(
    request: Request,
    page_id: str | None = None,
    limit: int = 20,
    page: int = 1,
    keyword: str | None = None,
) -> ConversationInfoResultSet:
    user_id = get_user_id(request)

    # get conversation visibility by user id
    visible_conversations = (
        await conversation_module._get_conversation_visibility_by_user_id(
            user_id, page, limit, keyword, show_section_conversations=False
        )
    )
    if len(visible_conversations['items']) == 0:
        return ConversationInfoResultSet(results=[], next_page_id=None)

    # Check if using database file store
    if config.file_store == 'database':
        # Use conversation records directly to create metadata objects
        filtered_results = []
        for conversation in visible_conversations['items']:
            try:
                # Support both dict and object
                conversation_id = getattr(
                    conversation, 'conversation_id', None
                ) or conversation.get('conversation_id')
                title = getattr(conversation, 'title', None) or conversation.get(
                    'title', ''
                )
                user_id = getattr(conversation, 'user_id', None) or conversation.get(
                    'user_id'
                )
                created_at = getattr(
                    conversation, 'created_at', None
                ) or conversation.get('created_at')

                conversation_metadata = ConversationMetadata(
                    conversation_id=conversation_id,
                    title=title,
                    user_id=user_id,
                    github_user_id=None,
                    selected_repository=None,
                    selected_branch=None,
                    created_at=created_at,
                    last_updated_at=created_at,
                )
                filtered_results.append(conversation_metadata)
            except Exception as e:
                logger.error(
                    f'Error creating metadata for conversation {conversation_id}: {e}'
                )
                continue
    else:
        # Use existing file-based approach
        conversation_store = await ConversationStoreImpl.get_instance(
            config, user_id, get_github_user_id(request)
        )

        visible_conversation_ids = [
            getattr(conversation, 'conversation_id', None)
            or conversation.get('conversation_id')
            for conversation in visible_conversations['items']
        ]

        conversation_metadata_result_set = await conversation_store.search(
            page_id, limit, filter_conversation_ids=visible_conversation_ids
        )

        # Filter out conversations older than max_age
        now = datetime.now(timezone.utc)
        max_age = config.conversation_max_age_seconds
        filtered_results = [
            conversation
            for conversation in conversation_metadata_result_set.results
            if hasattr(conversation, 'created_at')
            and (
                now - conversation.created_at.replace(tzinfo=timezone.utc)
            ).total_seconds()
            <= max_age
        ]

    conversation_ids = set(
        getattr(conversation, 'conversation_id', None) or conversation.conversation_id
        for conversation in filtered_results
    )
    running_conversations = await conversation_manager.get_running_agent_loops(
        get_user_id(request), set(conversation_ids)
    )
    result = ConversationInfoResultSet(
        results=await wait_all(
            _get_conversation_info(
                conversation=conversation,
                is_running=(
                    getattr(conversation, 'conversation_id', None)
                    or conversation.conversation_id
                )
                in running_conversations,
            )
            for conversation in filtered_results
        ),
        next_page_id=None,  # Database doesn't use page_id pagination
        total=visible_conversations['total'],
    )
    return result


@app.get('/conversations/{conversation_id}')
async def get_conversation(
    conversation_id: str, request: Request
) -> ConversationInfo | None:
    user_id = get_user_id(request)
    conversation_store = await ConversationStoreImpl.get_instance(
        config, user_id, get_github_user_id(request)
    )
    try:
        metadata = await conversation_store.get_metadata(conversation_id)
        is_running = await conversation_manager.is_agent_loop_running(conversation_id)
        conversation_info = await _get_conversation_info(metadata, is_running)
        if not conversation_info:
            logger.error(
                f'get_conversation: conversation {conversation_id} not found, attach_to_conversation returned None',
                extra={'session_id': conversation_id, 'user_id': user_id},
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f'Conversation {conversation_id} with user {user_id} not found',
            )
        # existed_conversation = await conversation_module._get_conversation_by_id(
        #     conversation_id, str(get_user_id(request))
        # )
        # if existed_conversation:
        #     conversation_info.research_mode = existed_conversation.configs.get('research_mode', None)
        return conversation_info
    except FileNotFoundError:
        return None


@app.patch('/conversations/{conversation_id}')
async def update_conversation(
    request: Request, conversation_id: str, title: str | None = Body(embed=True)
) -> bool:
    user_id = get_user_id(request)
    logger.info(
        f'Updating conversation {conversation_id} with title: {title}',
        extra={'session_id': conversation_id, 'user_id': user_id},
    )
    try:
        conversation_store = await ConversationStoreImpl.get_instance(
            config, user_id, get_github_user_id(request)
        )
        metadata = await conversation_store.get_metadata(conversation_id)
        if not metadata:
            logger.error(
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

        # current_metadata_title = metadata.title
        # if not metadata.title:
        #     metadata.title = get_default_conversation_title(conversation_id)

        # If title is empty or unspecified, auto-generate it
        if title:
            metadata.title = title
            await conversation_store.save_metadata(metadata)
            await conversation_module._update_title_conversation(
                conversation_id, metadata.title
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


@app.delete('/conversations/{conversation_id}')
async def delete_conversation(
    conversation_id: str,
    request: Request,
) -> bool:
    user_id = get_user_id(request)
    # conversation_store = await ConversationStoreImpl.get_instance(
    #     config, user_id, get_github_user_id(request)
    # )
    # try:
    #     await conversation_store.get_metadata(conversation_id)
    # except FileNotFoundError:
    #     return False
    is_running = await conversation_manager.is_agent_loop_running(conversation_id)
    if is_running:
        await conversation_manager.close_session(conversation_id)

    # disable delete conversation from runtime
    # runtime_cls = get_runtime_cls(config.runtime)
    # await runtime_cls.delete(conversation_id)
    # await conversation_store.delete_metadata(conversation_id)

    # delete conversation from databasedatab
    await delete_thread(
        conversation_id,
        request.headers.get('Authorization'),
        request.headers.get('x-device-id'),
    )
    await conversation_module._delete_conversation(conversation_id, str(user_id))

    return True


@app.patch('/conversations/{conversation_id}/change-visibility')
async def change_visibility(
    conversation_id: str,
    request: Request,
    is_published: bool = Form(...),
    hidden_prompt: bool = Form(...),
    file: Optional[UploadFile] = None,
) -> bool:
    user_id = get_user_id(request)
    conversation_store = await ConversationStoreImpl.get_instance(
        config, user_id, get_github_user_id(request)
    )
    metadata = await conversation_store.get_metadata(conversation_id)
    if not metadata:
        return False

    # Handle file upload if provided
    extra_data = {
        'hidden_prompt': hidden_prompt,
    }

    if file and s3_handler is not None:
        print('processing file:', file)
        folder_path = f'conversations/{conversation_id}'
        file_url = await s3_handler.upload_file(file, folder_path)
        if file_url:
            extra_data['thumbnail_url'] = file_url

    await change_thread_visibility(
        conversation_id,
        is_published,
        request.headers.get('Authorization'),
        request.headers.get('x-device-id'),
    )

    return await conversation_module._update_conversation_visibility(
        conversation_id,
        is_published,
        str(user_id),
        extra_data,
        metadata.title if metadata.title else '',
    )


@app.get(
    '/conversations/{conversation_id}/visibility', response_model=ConversationVisibility
)
async def get_conversation_visibility(
    conversation_id: str,
    request: Request,
) -> bool:
    user_id = get_user_id(request)
    return await conversation_module._get_conversation_visibility(
        conversation_id, str(user_id)
    )


async def _get_conversation_info(
    conversation: ConversationMetadata,
    is_running: bool,
) -> ConversationInfo | None:
    try:
        title = conversation.title
        if not title:
            title = get_default_conversation_title(conversation.conversation_id)
        return ConversationInfo(
            conversation_id=conversation.conversation_id,
            title=title,
            last_updated_at=conversation.last_updated_at,
            created_at=conversation.created_at,
            selected_repository=conversation.selected_repository,
            status=(
                ConversationStatus.RUNNING if is_running else ConversationStatus.STOPPED
            ),
        )
    except Exception as e:
        logger.error(
            f'Error loading conversation {conversation.conversation_id}: {str(e)}',
            extra={'session_id': conversation.conversation_id},
        )
        return None
