from fastapi import APIRouter
from openhands.llm import bedrock
from openhands.core.config import LLMConfig
from openhands.controller.agent import Agent
from openhands.security.options import SecurityAnalyzers
from openhands.core.logger import openhands_logger as logger
import requests

router = APIRouter()

@router.get('/models')
async def get_litellm_models(config) -> list[str]:
    litellm_model_list = litellm.model_list + list(litellm.model_cost.keys())
    litellm_model_list_without_bedrock = bedrock.remove_error_modelId(
        litellm_model_list
    )
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
                logger.error(f'Error getting OLLAMA models: {e}', exc_info=True)

    return list(sorted(set(model_list)))

@router.get('/agents')
async def get_agents():
    agents = sorted(Agent.list_agents())
    return agents

@router.get('/security-analyzers')
async def get_security_analyzers():
    return sorted(SecurityAnalyzers.keys())
