import warnings

import requests

from openhands.security.options import SecurityAnalyzers

with warnings.catch_warnings():
    warnings.simplefilter('ignore')
    import litellm

from fastapi import (
    APIRouter,
)

from openhands.controller.agent import Agent
from openhands.core.config import LLMConfig
from openhands.core.logger import openhands_logger as logger
from openhands.llm import bedrock
from openhands.server.shared import config, openhands_config

app = APIRouter(prefix='/api/options')


@app.get('/models')
async def get_litellm_models() -> list[str]:
    """
    Get all models supported by LiteLLM.

    This function combines models from litellm and Bedrock, removing any
    error-prone Bedrock models.

    To get the models:
    ```sh
    curl http://localhost:3000/api/litellm-models
    ```

    Returns:
        list: A sorted list of unique model names.
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
            llm_config.aws_access_key_id,
            llm_config.aws_secret_access_key,
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


@app.get('/agents')
async def get_agents():
    """Get all agents supported by LiteLLM.

    To get the agents:
    ```sh
    curl http://localhost:3000/api/agents
    ```

    Returns:
        list: A sorted list of agent names.
    """
    agents = sorted(Agent.list_agents())
    return agents


@app.get('/security-analyzers')
async def get_security_analyzers():
    """Get all supported security analyzers.

    To get the security analyzers:
    ```sh
    curl http://localhost:3000/api/security-analyzers
    ```

    Returns:
        list: A sorted list of security analyzer names.
    """
    return sorted(SecurityAnalyzers.keys())


@app.get('/config')
async def get_config():
    """
    Get current config
    """

    return openhands_config.get_config()
