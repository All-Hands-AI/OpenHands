import warnings

import httpx

with warnings.catch_warnings():
    warnings.simplefilter('ignore')
    import litellm

from openhands.core.config import LLMConfig, OpenHandsConfig
from openhands.core.logger import openhands_logger as logger
from openhands.llm import bedrock


def _strength_score(model_id: str) -> int:
    """Assign a relative strength score for sorting models (higher = stronger).
    This is a heuristic ordering to surface the most capable models first in the UI.
    """
    mid = model_id.lower()
    # Highest tier (future and frontier models)
    if 'gpt-5' in mid:
        return 1000
    if 'o3' in mid or 'opus-4' in mid or 'sonnet-4' in mid:
        return 950
    # Premium reasoning and latest flagship
    if 'gemini-2.5-pro' in mid:
        return 900
    if 'gpt-4o' in mid or 'gpt4o' in mid:
        return 850
    if 'mistral-large' in mid or 'mistral-large-latest' in mid:
        return 800
    # Solid general models
    if 'qwen3' in mid or 'qwen-3' in mid:
        return 700
    if 'o4-mini' in mid or 'mini' in mid:
        return 650
    # Dev/experimental
    if 'devstral' in mid:
        return 600
    # Fallback
    return 100


def get_supported_llm_models(config: OpenHandsConfig) -> list[str]:
    """Get all models supported by LiteLLM.

    This function combines models from litellm and Bedrock, removing any
    error-prone Bedrock models.

    Returns:
        list[str]: A list of unique model names, sorted by strength (strongest first).
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
                ollama_models_list = httpx.get(ollama_url, timeout=3).json()['models']  # noqa: ASYNC100
                for model in ollama_models_list:
                    model_list.append('ollama/' + model['name'])
                break
            except httpx.HTTPError as e:
                logger.error(f'Error getting OLLAMA models: {e}')

    # Add OpenHands provider models
    openhands_models = [
        'openhands/claude-sonnet-4-20250514',
        'openhands/gpt-5-2025-08-07',
        'openhands/claude-opus-4-20250514',
        'openhands/gemini-2.5-pro',
        'openhands/o3',
        'openhands/o4-mini',
        'openhands/devstral-small-2505',
        'openhands/devstral-small-2507',
        'openhands/devstral-medium-2507',
        'openhands/kimi-k2-0711-preview',
        'openhands/qwen3-coder-480b',
    ]
    model_list = openhands_models + model_list

    unique_models = list(set(model_list))
    # Sort strongest -> weakest, and then alphabetically for ties for stability
    unique_models.sort(key=lambda m: (-_strength_score(m), m))

    return unique_models
