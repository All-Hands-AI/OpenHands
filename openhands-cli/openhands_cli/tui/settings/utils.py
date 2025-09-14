import litellm
from openhands_cli.tui.settings.constants import VERIFIED_ANTHROPIC_MODELS, VERIFIED_MISTRAL_MODELS, VERIFIED_OPENAI_MODELS, VERIFIED_OPENHANDS_MODELS
from pydantic import BaseModel, Field


def split_is_actually_version(split: list[str]) -> bool:
    return (
        len(split) > 1
        and bool(split[1])
        and bool(split[1][0])
        and split[1][0].isdigit()
    )

class ModelInfo(BaseModel):
    """Information about a model and its provider."""

    provider: str = Field(description='The provider of the model')
    model: str = Field(description='The model identifier')
    separator: str = Field(description='The separator used in the model identifier')

    def __getitem__(self, key: str) -> str:
        """Allow dictionary-like access to fields."""
        if key == 'provider':
            return self.provider
        elif key == 'model':
            return self.model
        elif key == 'separator':
            return self.separator
        raise KeyError(f'ModelInfo has no key {key}')


class ProviderInfo(BaseModel):
    """Information about a provider and its models."""

    separator: str = Field(description='The separator used in model identifiers')
    models: list[str] = Field(
        default_factory=list, description='List of model identifiers'
    )

    def __getitem__(self, key: str) -> str | list[str]:
        """Allow dictionary-like access to fields."""
        if key == 'separator':
            return self.separator
        elif key == 'models':
            return self.models
        raise KeyError(f'ProviderInfo has no key {key}')

    def get(self, key: str, default: None = None) -> str | list[str] | None:
        """Dictionary-like get method with default value."""
        try:
            return self[key]
        except KeyError:
            return default


def extract_model_and_provider(model: str) -> ModelInfo:
    """Extract provider and model information from a model identifier.

    Args:
        model: The model identifier string

    Returns:
        A ModelInfo object containing provider, model, and separator information
    """
    separator = '/'
    split = model.split(separator)

    if len(split) == 1:
        # no "/" separator found, try with "."
        separator = '.'
        split = model.split(separator)
        if split_is_actually_version(split):
            split = [separator.join(split)]  # undo the split

    if len(split) == 1:
        # no "/" or "." separator found
        if split[0] in VERIFIED_OPENAI_MODELS:
            return ModelInfo(provider='openai', model=split[0], separator='/')
        if split[0] in VERIFIED_ANTHROPIC_MODELS:
            return ModelInfo(provider='anthropic', model=split[0], separator='/')
        if split[0] in VERIFIED_MISTRAL_MODELS:
            return ModelInfo(provider='mistral', model=split[0], separator='/')
        if split[0] in VERIFIED_OPENHANDS_MODELS:
            return ModelInfo(provider='openhands', model=split[0], separator='/')
        # return as model only
        return ModelInfo(provider='', model=model, separator='')

    provider = split[0]
    model_id = separator.join(split[1:])
    return ModelInfo(provider=provider, model=model_id, separator=separator)


def organize_models_and_providers(
    models: list[str],
) -> dict[str, 'ProviderInfo']:
    """Organize a list of model identifiers by provider.

    Args:
        models: List of model identifiers

    Returns:
        A mapping of providers to their information and models
    """
    result_dict: dict[str, ProviderInfo] = {}

    for model in models:
        extracted = extract_model_and_provider(model)
        separator = extracted.separator
        provider = extracted.provider
        model_id = extracted.model

        # Ignore "anthropic" providers with a separator of "."
        # These are outdated and incompatible providers.
        if provider == 'anthropic' and separator == '.':
            continue

        key = provider or 'other'
        if key not in result_dict:
            result_dict[key] = ProviderInfo(separator=separator, models=[])

        result_dict[key].models.append(model_id)

    return result_dict

def get_supported_llm_models() -> list[str]:
    """Get all models supported by LiteLLM.

    Returns:
        list[str]: A sorted list of unique model names.
    """
    model_list = litellm.model_list + list(litellm.model_cost.keys())
    # TODO: get bedrock and ollama models

    # Add OpenHands provider models
    openhands_models = [
        'openhands/claude-sonnet-4-20250514',
        'openhands/gpt-5-2025-08-07',
        'openhands/gpt-5-mini-2025-08-07',
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

    return list(sorted(set(model_list)))
