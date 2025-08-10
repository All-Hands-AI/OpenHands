from typing import Any

from fastapi import APIRouter, Depends

from openhands.controller.agent import Agent
from openhands.security.options import SecurityAnalyzers
from openhands.server.dependencies import get_dependencies
from openhands.server.shared import config, server_config, conversation_manager
from openhands.server.routes.manage_conversations import InitSessionRequest, new_conversation
from openhands.server.user_auth import (
    get_auth_type,
    get_provider_tokens,
    get_user_id,
    get_user_secrets,
)
from openhands.server.user_auth.user_auth import AuthType
from openhands.integrations.provider import PROVIDER_TOKEN_TYPE
from openhands.storage.data_models.user_secrets import UserSecrets
from openhands.utils.llm import get_supported_llm_models

app = APIRouter(prefix='/api/options', dependencies=get_dependencies())


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
    return get_supported_llm_models(config)


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


# Friendly wrappers for sessions and commands
@app.post('/sessions', response_model=dict[str, str])
async def create_session(
    data: InitSessionRequest,
    user_id: str | None = Depends(get_user_id),
    provider_tokens: PROVIDER_TOKEN_TYPE = Depends(get_provider_tokens),
    user_secrets: UserSecrets | None = Depends(get_user_secrets),
    auth_type: AuthType | None = Depends(get_auth_type),
) -> dict[str, str]:
    resp = await new_conversation(
        data,
        user_id,  # type: ignore[arg-type]
        provider_tokens,  # type: ignore[arg-type]
        user_secrets,  # type: ignore[arg-type]
        auth_type,  # type: ignore[arg-type]
    )
    return {'conversation_id': resp.conversation_id}


@app.post('/commands', response_model=dict[str, bool])
async def send_command(conversation_id: str, command: dict[str, Any]) -> dict[str, bool]:
    await conversation_manager.send_event_to_conversation(conversation_id, command)
    return {'ok': True}
