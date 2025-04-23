from pathlib import Path

import toml

from openhands.core.cli_tui import (
    UsageMetrics,
)
from openhands.events.event import Event
from openhands.llm.metrics import Metrics


def manage_openhands_file(folder_path=None, add_to_trusted=False):
    openhands_file = Path.home() / '.openhands.toml'
    default_content: dict = {'trusted_dirs': []}

    if not openhands_file.exists():
        with open(openhands_file, 'w') as f:
            toml.dump(default_content, f)

    if folder_path:
        with open(openhands_file, 'r') as f:
            try:
                config = toml.load(f)
            except Exception:
                config = default_content

        if 'trusted_dirs' not in config:
            config['trusted_dirs'] = []

        if folder_path in config['trusted_dirs']:
            return True

        if add_to_trusted:
            config['trusted_dirs'].append(folder_path)
            with open(openhands_file, 'w') as f:
                toml.dump(config, f)

        return False

    return False


def update_usage_metrics(event: Event, usage_metrics: UsageMetrics):
    if not hasattr(event, 'llm_metrics'):
        return

    llm_metrics: Metrics | None = event.llm_metrics
    if not llm_metrics:
        return

    usage_metrics.metrics = llm_metrics


def extract_model_and_provider(model):
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
            return {'provider': 'openai', 'model': split[0], 'separator': '/'}
        if split[0] in VERIFIED_ANTHROPIC_MODELS:
            return {'provider': 'anthropic', 'model': split[0], 'separator': '/'}
        # return as model only
        return {'provider': '', 'model': model, 'separator': ''}

    provider = split[0]
    model_id = separator.join(split[1:])
    return {'provider': provider, 'model': model_id, 'separator': separator}


def organize_models_and_providers(models):
    result = {}

    for model in models:
        extracted = extract_model_and_provider(model)
        separator = extracted['separator']
        provider = extracted['provider']
        model_id = extracted['model']

        # Ignore "anthropic" providers with a separator of "."
        # These are outdated and incompatible providers.
        if provider == 'anthropic' and separator == '.':
            continue

        key = provider or 'other'
        if key not in result:
            result[key] = {'separator': separator, 'models': []}

        result[key]['models'].append(model_id)

    return result


VERIFIED_PROVIDERS = ['openai', 'azure', 'anthropic', 'deepseek']

VERIFIED_OPENAI_MODELS = [
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
    'claude-2',
    'claude-2.1',
    'claude-3-5-sonnet-20240620',
    'claude-3-5-sonnet-20241022',
    'claude-3-5-haiku-20241022',
    'claude-3-haiku-20240307',
    'claude-3-opus-20240229',
    'claude-3-sonnet-20240229',
    'claude-3-7-sonnet-20250219',
]


def is_number(char):
    return char.isdigit()


def split_is_actually_version(split):
    return len(split) > 1 and split[1] and split[1][0] and is_number(split[1][0])


def read_file(file_path):
    with open(file_path, 'r') as f:
        return f.read()


def write_to_file(file_path, content):
    with open(file_path, 'w') as f:
        f.write(content)
