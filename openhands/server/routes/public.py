import warnings
from typing import Annotated, Any, cast

import requests
from fastapi import APIRouter, Depends, Response
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute

from openhands.security.options import SecurityAnalyzers

with warnings.catch_warnings():
    warnings.simplefilter('ignore')
    import litellm

from openhands.controller.agent import Agent
from openhands.core.config import LLMConfig
from openhands.core.logger import openhands_logger as logger
from openhands.llm import bedrock
from openhands.server.shared import config, server_config

app = APIRouter(prefix='/api/options')


async def get_litellm_models_list() -> list[str]:
    """Get all models supported by LiteLLM.

    This function combines models from litellm and Bedrock, removing any
    error-prone Bedrock models.

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
                ollama_models_list = requests.get(ollama_url, timeout=3).json()[
                    'models'
                ]
                for model in ollama_models_list:
                    model_list.append('ollama/' + model['name'])
                break
            except requests.exceptions.RequestException as e:
                logger.error(f'Error getting OLLAMA models: {e}')

    return list(sorted(set(model_list)))


def get_models_route() -> APIRoute:
    """Get the route for getting models.

    Returns:
        APIRoute: The route for getting models.
    """
    return cast(
        APIRoute,
        app.get('/models', response_model=list[str]),
    )


async def get_litellm_models(
    models: Annotated[list[str], Depends(get_litellm_models_list)],
) -> list[str]:
    """Get all models supported by LiteLLM.

    To get the models:
    ```sh
    curl http://localhost:3000/api/litellm-models
    ```

    Args:
        models (list[str]): The list of models from get_litellm_models_list.

    Returns:
        list[str]: A sorted list of unique model names.
    """
    return models


models_route = get_models_route()
models_route.endpoint = get_litellm_models


async def get_agents_list() -> list[str]:
    """Get all agents supported by LiteLLM.

    Returns:
        list[str]: A sorted list of agent names.
    """
    return sorted(Agent.list_agents())


def get_agents_route() -> APIRoute:
    """Get the route for getting agents.

    Returns:
        APIRoute: The route for getting agents.
    """
    return cast(
        APIRoute,
        app.get('/agents', response_model=list[str]),
    )


async def get_agents(
    agents: Annotated[list[str], Depends(get_agents_list)],
) -> list[str]:
    """Get all agents supported by LiteLLM.

    To get the agents:
    ```sh
    curl http://localhost:3000/api/agents
    ```

    Args:
        agents (list[str]): The list of agents from get_agents_list.

    Returns:
        list[str]: A sorted list of agent names.
    """
    return agents


agents_route = get_agents_route()
agents_route.endpoint = get_agents


async def get_security_analyzers_list() -> list[str]:
    """Get all supported security analyzers.

    Returns:
        list[str]: A sorted list of security analyzer names.
    """
    return sorted(SecurityAnalyzers.keys())


def get_analyzers_route() -> APIRoute:
    """Get the route for getting security analyzers.

    Returns:
        APIRoute: The route for getting security analyzers.
    """
    return cast(
        APIRoute,
        app.get('/security-analyzers', response_model=list[str]),
    )


async def get_security_analyzers(
    analyzers: Annotated[list[str], Depends(get_security_analyzers_list)],
) -> list[str]:
    """Get all supported security analyzers.

    To get the security analyzers:
    ```sh
    curl http://localhost:3000/api/security-analyzers
    ```

    Args:
        analyzers (list[str]): The list of analyzers from get_security_analyzers_list.

    Returns:
        list[str]: A sorted list of security analyzer names.
    """
    return analyzers


analyzers_route = get_analyzers_route()
analyzers_route.endpoint = get_security_analyzers


async def get_server_config() -> Response:
    """Get current config.

    Returns:
        Response: The current server configuration.
    """
    config_data = server_config.get_config()
    return JSONResponse(
        status_code=200,
        content=config_data,
    )


def get_config_route() -> APIRoute:
    """Get the route for getting config.

    Returns:
        APIRoute: The route for getting config.
    """
    return cast(
        APIRoute,
        app.get('/config', response_model=dict[str, Any]),
    )


async def get_config(
    response: Annotated[Response, Depends(get_server_config)],
) -> Response:
    """Get current config.

    Args:
        response (Response): The response from get_server_config.

    Returns:
        Response: The current server configuration.
    """
    return response


config_route = get_config_route()
config_route.endpoint = get_config
