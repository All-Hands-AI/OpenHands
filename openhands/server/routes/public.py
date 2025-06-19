import base64
import os
import warnings
from datetime import datetime, timezone
from typing import Any, Optional

import aiofiles  # type: ignore
from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import JSONResponse
from pathspec import PathSpec
from pathspec.patterns import GitWildMatchPattern

from openhands.core.exceptions import AgentRuntimeUnavailableError
from openhands.events.action.agent import RecallAction
from openhands.events.action.empty import NullAction
from openhands.events.action.files import FileReadAction
from openhands.events.async_event_store_wrapper import AsyncEventStoreWrapper
from openhands.events.event_store import EventStore
from openhands.events.observation.agent import AgentStateChangedObservation
from openhands.events.observation.empty import NullObservation
from openhands.events.observation.error import ErrorObservation
from openhands.events.observation.files import FileReadObservation
from openhands.events.serialization.event import event_to_dict
from openhands.runtime.base import Runtime
from openhands.security.options import SecurityAnalyzers
from openhands.server import shared
from openhands.server.data_models.conversation_info import ConversationInfo
from openhands.server.data_models.conversation_info_result_set import (
    ConversationInfoResultSet,
)
from openhands.server.file_config import FILES_TO_IGNORE
from openhands.server.modules.conversation import conversation_module
from openhands.server.routes.manage_conversations import _get_conversation_info
from openhands.server.shared import (
    conversation_manager,
)

with warnings.catch_warnings():
    warnings.simplefilter('ignore')
    import litellm
import aiohttp

from openhands.controller.agent import Agent
from openhands.core.config import LLMConfig
from openhands.core.logger import openhands_logger as logger
from openhands.llm import bedrock
from openhands.server.shared import ConversationStoreImpl, config, server_config
from openhands.utils.async_utils import call_sync_from_async, wait_all

app = APIRouter(prefix='/api/options')


def verify_thesis_backend_server(api_key: str = Header(..., alias='x-key-oh')):
    expected_key = os.getenv('KEY_THESIS_BACKEND_SERVER')
    if api_key != expected_key:
        raise HTTPException(status_code=401, detail='Invalid API key')


@app.get('/models', response_model=list[str])
async def get_litellm_models() -> list[str]:
    """Get all models supported by LiteLLM.

    This function combines models from litellm and Bedrock, removing any
    error-prone Bedrock models.

    To get the models:
    ```sh
    curl http://localhost:3000/api/litellm-models
    ```

    Returns:
        list[str]: A sorted list of unique model names.
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
            llm_config.aws_access_key_id.get_secret_value(),
            llm_config.aws_secret_access_key.get_secret_value(),
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
                async with aiohttp.ClientSession() as session:
                    async with session.get(ollama_url, timeout=3) as response:
                        ollama_models_list = await response.json()['models']
                        for model in ollama_models_list:
                            model_list.append('ollama/' + model['name'])
                        break
            except aiohttp.ClientError as e:
                logger.error(f'Error getting OLLAMA models: {e}')

    return list(sorted(set(model_list)))


@app.get('/agents', response_model=list[str])
async def get_agents() -> list[str]:
    """Get all agents supported by LiteLLM.

    To get the agents:
    ```sh
    curl http://localhost:3000/api/agents
    ```

    Returns:
        list[str]: A sorted list of agent names.
    """
    return sorted(Agent.list_agents())


@app.get('/security-analyzers', response_model=list[str])
async def get_security_analyzers() -> list[str]:
    """Get all supported security analyzers.

    To get the security analyzers:
    ```sh
    curl http://localhost:3000/api/security-analyzers
    ```

    Returns:
        list[str]: A sorted list of security analyzer names.
    """
    return sorted(SecurityAnalyzers.keys())


@app.get('/config', response_model=dict[str, Any])
async def get_config() -> dict[str, Any]:
    """Get current config.

    Returns:
        dict[str, Any]: The current server configuration.
    """
    return server_config.get_config()


@app.get('/use-cases', response_model=ConversationInfoResultSet)
async def get_conversations(
    user_address: Optional[str] = os.getenv('USER_USE_CASE_SAMPLE'),
    limit: int = 8,
) -> ConversationInfoResultSet:
    """Get list of conversations for a user.

    Args:
        user_address (str): The user's wallet address
        limit (int, optional): Maximum number of conversations to return. Defaults to 10.

    Returns:
        ConversationInfoResultSet: List of conversations and pagination info

    Raises:
        HTTPException: If there's an error fetching conversations
    """
    try:
        conversation_store = await ConversationStoreImpl.get_instance(
            config, user_address, None
        )

        conversation_metadata_result_set = await conversation_store.search(None, limit)
        # Filter conversations by age
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

        # Get running conversation IDs
        conversation_ids = set(
            conversation.conversation_id for conversation in filtered_results
        )
        running_conversations = await conversation_manager.get_running_agent_loops(
            user_address, conversation_ids
        )

        # Build final result
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

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f'Error fetching conversations: {str(e)}'
        )


@app.get('/use-cases/conversations/{conversation_id}')
async def get_conversation(
    conversation_id: str,
) -> ConversationInfo | None:
    if not conversation_id:
        raise HTTPException(status_code=400, detail='Conversation ID is required')
    whitelisted_user_id = os.getenv('USER_USE_CASE_SAMPLE')
    conversation_store = await ConversationStoreImpl.get_instance(
        config, whitelisted_user_id, None
    )
    try:
        metadata = await conversation_store.get_metadata(conversation_id)
        is_running = await conversation_manager.is_agent_loop_running(conversation_id)
        conversation_info = await _get_conversation_info(metadata, is_running)
        return conversation_info
    except FileNotFoundError:
        return None


@app.get('/conversations/events/{conversation_id}')
async def get_conversation_events(
    conversation_id: str,
    x_key_oh: str = Depends(verify_thesis_backend_server),
) -> Any:
    conversation = await conversation_module._get_conversation_by_id(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail='Conversation not found')

    # eventstore
    event_store = EventStore(
        conversation_id,
        conversation_manager.file_store,
        conversation.user_id,
    )
    if not event_store:
        raise HTTPException(status_code=404, detail='Event store not found')
    async_store = AsyncEventStoreWrapper(event_store, 0)
    result = []
    async for event in async_store:
        try:
            if isinstance(
                event,
                (
                    NullAction,
                    NullObservation,
                    RecallAction,
                    AgentStateChangedObservation,
                ),
            ):
                continue
            event_dict = event_to_dict(event)
            if (
                event_dict.get('source') == 'user'
                or event_dict.get('source') == 'agent'
            ):
                result.append(event_dict)
        except Exception as e:
            logger.error(f'Error converting event to dict: {str(e)}')
    return result


@app.get('/conversations/list-files-internal/{conversation_id}')
async def list_files(
    conversation_id: str,
    # request: Request,
    path: str | None = None,
    x_key_oh: str = Depends(verify_thesis_backend_server),
) -> Any:
    conversation = await conversation_module._get_conversation_by_id(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail='Conversation not found')

    session = await shared.conversation_manager.attach_to_conversation(
        conversation_id, conversation.user_id
    )

    if not session:
        return JSONResponse(
            status_code=404,
            content={'error': 'Session not found'},
        )

    try:
        if not session.runtime:
            return JSONResponse(
                status_code=404,
                content={'error': 'Runtime not yet initialized'},
            )
        runtime: Runtime = session.runtime

        try:
            file_list = await call_sync_from_async(runtime.list_files, path)
        except AgentRuntimeUnavailableError as e:
            logger.error(f'Error listing files: {e}')
            return JSONResponse(
                status_code=500,
                content={'error': f'Error listing files: {e}'},
            )
        if path:
            file_list = [os.path.join(path, f) for f in file_list]

        file_list = [f for f in file_list if f not in FILES_TO_IGNORE]

        async def filter_for_gitignore(file_list, base_path):
            gitignore_path = os.path.join(base_path, '.gitignore')
            try:
                read_action = FileReadAction(gitignore_path)
                observation = await call_sync_from_async(
                    runtime.run_action, read_action
                )
                spec = PathSpec.from_lines(
                    GitWildMatchPattern, observation.content.splitlines()
                )
            except Exception as e:
                logger.warning(e)
                return file_list
            file_list = [entry for entry in file_list if not spec.match_file(entry)]
            return file_list

        try:
            file_list = await filter_for_gitignore(file_list, '')
        except AgentRuntimeUnavailableError as e:
            logger.error(f'Error filtering files: {e}')
            return JSONResponse(
                status_code=500,
                content={'error': f'Error filtering files: {e}'},
            )
        return file_list
    finally:
        if session:
            await shared.conversation_manager.detach_from_conversation(session)


@app.get('/conversations/select-file-internal/{conversation_id}')
async def select_file(
    conversation_id: str,
    file: str,
    x_key_oh: str = Depends(verify_thesis_backend_server),
) -> Any:
    conversation = await conversation_module._get_conversation_by_id(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail='Conversation not found')

    session = await shared.conversation_manager.attach_to_conversation(
        conversation_id, conversation.user_id
    )
    if not session:
        return JSONResponse(
            status_code=404,
            content={'error': 'Session not found'},
        )

    try:
        if not session.runtime:
            return JSONResponse(
                status_code=404,
                content={'error': 'Runtime not yet initialized'},
            )
        runtime: Runtime = session.runtime

        file = os.path.join(
            runtime.config.workspace_mount_path_in_sandbox + '/' + runtime.sid, file
        )
        read_action = FileReadAction(file)
        try:
            observation = await call_sync_from_async(runtime.run_action, read_action)
        except AgentRuntimeUnavailableError as e:
            logger.error(f'Error opening file {file}: {e}')
            return JSONResponse(
                status_code=500,
                content={'error': f'Error opening file: {e}'},
            )

        if isinstance(observation, FileReadObservation):
            content = observation.content
            return {'code': content}
        elif isinstance(observation, ErrorObservation):
            logger.error(f'Error opening file {file}: {observation}')

            if 'ERROR_BINARY_FILE' in observation.message:
                try:
                    async with aiofiles.open(file, 'rb') as f:
                        binary_data = await f.read()
                        base64_encoded = base64.b64encode(binary_data).decode('utf-8')
                        return {'code': base64_encoded}
                except Exception as e:
                    return JSONResponse(
                        status_code=500,
                        content={'error': f'Error reading binary file: {e}'},
                    )
            else:
                return JSONResponse(
                    status_code=500,
                    content={'error': f'Error opening file: {observation}'},
                )

        return JSONResponse(
            status_code=500,
            content={'error': f'Error opening file: {observation}'},
        )
    finally:
        if session:
            await shared.conversation_manager.detach_from_conversation(session)


@app.put('/update-empty-titles')
async def update_empty_titles(
    x_key_oh: str = Depends(verify_thesis_backend_server),
) -> dict[str, Any]:
    result = await conversation_module.update_empty_conversation_titles(config)
    return result
