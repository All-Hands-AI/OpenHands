import os
import warnings
from datetime import datetime, timezone
from typing import Any, Optional

import httpx
from fastapi import APIRouter, HTTPException

from openhands.security.options import SecurityAnalyzers
from openhands.server.data_models.conversation_info import ConversationInfo
from openhands.server.data_models.conversation_info_result_set import (
    ConversationInfoResultSet,
)
from openhands.server.routes.manage_conversations import _get_conversation_info
from openhands.server.shared import (
    conversation_manager,
)

with warnings.catch_warnings():
    warnings.simplefilter('ignore')
    import litellm
from openhands.controller.agent import Agent
from openhands.core.config import LLMConfig
from openhands.core.logger import openhands_logger as logger
from openhands.llm import bedrock
from openhands.server.shared import ConversationStoreImpl, config, server_config
from openhands.utils.async_utils import wait_all

app = APIRouter(prefix='/api/options')


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
                ollama_models_list = httpx.get(ollama_url, timeout=3).json()['models']
                for model in ollama_models_list:
                    model_list.append('ollama/' + model['name'])
                break
            except httpx.HTTPError as e:
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
    conversation_id: str | None = None,
) -> ConversationInfo | None:
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
