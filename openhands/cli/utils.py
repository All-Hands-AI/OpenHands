from pathlib import Path

import toml
from pydantic import BaseModel, Field

from openhands.cli.tui import (
    UsageMetrics,
)
from openhands.events.event import Event
from openhands.llm.metrics import Metrics

_LOCAL_CONFIG_FILE_PATH = Path.home() / '.openhands' / 'config.toml'
_DEFAULT_CONFIG: dict[str, dict[str, list[str]]] = {'sandbox': {'trusted_dirs': []}}


def get_local_config_trusted_dirs() -> list[str]:
    if _LOCAL_CONFIG_FILE_PATH.exists():
        with open(_LOCAL_CONFIG_FILE_PATH, 'r') as f:
            try:
                config = toml.load(f)
            except Exception:
                config = _DEFAULT_CONFIG
        if 'sandbox' in config and 'trusted_dirs' in config['sandbox']:
            return config['sandbox']['trusted_dirs']
    return []


def add_local_config_trusted_dir(folder_path: str) -> None:
    config = _DEFAULT_CONFIG
    if _LOCAL_CONFIG_FILE_PATH.exists():
        try:
            with open(_LOCAL_CONFIG_FILE_PATH, 'r') as f:
                config = toml.load(f)
        except Exception:
            config = _DEFAULT_CONFIG
    else:
        _LOCAL_CONFIG_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)

    if 'sandbox' not in config:
        config['sandbox'] = {}
    if 'trusted_dirs' not in config['sandbox']:
        config['sandbox']['trusted_dirs'] = []

    if folder_path not in config['sandbox']['trusted_dirs']:
        config['sandbox']['trusted_dirs'].append(folder_path)

    with open(_LOCAL_CONFIG_FILE_PATH, 'w') as f:
        toml.dump(config, f)


def update_usage_metrics(event: Event, usage_metrics: UsageMetrics) -> None:
    if not hasattr(event, 'llm_metrics'):
        return

    llm_metrics: Metrics | None = event.llm_metrics
    if not llm_metrics:
        return

    usage_metrics.metrics = llm_metrics


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


VERIFIED_PROVIDERS = ['anthropic', 'openai', 'mistral']

VERIFIED_OPENAI_MODELS = [
    'o4-mini',
    'gpt-4o',
    'gpt-4o-mini',
    'gpt-4-turbo',
    'gpt-4',
    'gpt-4-32k',
    'o1-mini',
    'o1',
    'o3-mini',
    'o3-mini-2025-01-31',
]

VERIFIED_ANTHROPIC_MODELS = [
    'claude-sonnet-4-20250514',
    'claude-opus-4-20250514',
    'claude-3-7-sonnet-20250219',
    'claude-3-sonnet-20240229',
    'claude-3-opus-20240229',
    'claude-3-haiku-20240307',
    'claude-3-5-haiku-20241022',
    'claude-3-5-sonnet-20241022',
    'claude-3-5-sonnet-20240620',
    'claude-2.1',
    'claude-2',
]

VERIFIED_MISTRAL_MODELS = [
    'devstral-small-2505',
]


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


def is_number(char: str) -> bool:
    return char.isdigit()


def split_is_actually_version(split: list[str]) -> bool:
    return (
        len(split) > 1
        and bool(split[1])
        and bool(split[1][0])
        and is_number(split[1][0])
    )


def read_file(file_path: str | Path) -> str:
    with open(file_path, 'r') as f:
        return f.read()


def write_to_file(file_path: str | Path, content: str) -> None:
    with open(file_path, 'w') as f:
        f.write(content)
