from typing import Any

from fastapi import APIRouter, Request
from pydantic import BaseModel

from openhands.controller.agent import Agent
from openhands.microagent.microagent import KnowledgeMicroagent, TaskMicroagent
from openhands.security.options import SecurityAnalyzers
from openhands.server.shared import config, server_config
from openhands.utils.llm import get_supported_llm_models

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


class MicroagentInfo(BaseModel):
    name: str
    trigger: str
    description: str


@app.get('/microagents', response_model=list[dict[str, str]])
async def get_microagents(
    request: Request,
) -> list[dict[str, str]]:
    """Get all available microagents for the current session.

    To get the microagents:
    ```sh
    curl http://localhost:3000/api/options/microagents
    ```

    Returns:
        List[Dict[str, str]]: A list of microagent information including name and trigger.
    """
    # Check if we have a conversation in the request state
    if not hasattr(request.state, 'conversation') or not request.state.conversation:
        return []

    # Get the runtime from the conversation
    if (
        not hasattr(request.state.conversation, 'runtime')
        or not request.state.conversation.runtime
    ):
        return []

    # Get the agent session from the runtime
    runtime = request.state.conversation.runtime
    if not hasattr(runtime, 'agent_session') or not runtime.agent_session:
        return []

    # Get the memory from the agent session
    agent_session = runtime.agent_session
    if not hasattr(agent_session, 'memory') or not agent_session.memory:
        return []

    # Get all knowledge microagents from memory
    microagents = []
    for agent in agent_session.memory.knowledge_microagents.values():
        if isinstance(agent, (KnowledgeMicroagent, TaskMicroagent)) and agent.triggers:
            # Use the first trigger as the main one
            trigger = agent.triggers[0]
            # Extract a short description from the content (first line or paragraph)
            description = agent.content.strip().split('\n')[0][:100]

            microagents.append(
                {'name': agent.name, 'trigger': trigger, 'description': description}
            )

    return microagents
