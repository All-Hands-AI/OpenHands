from enum import Enum

from openhands_cli.user_actions.types import UserConfirmation
from openhands_cli.user_actions.utils import cli_confirm, prompt_user, prompt_with_completer

from openhands_cli.tui.settings.constants import (
    VERIFIED_PROVIDERS,
    VERIFIED_OPENAI_MODELS,
    VERIFIED_ANTHROPIC_MODELS,
    VERIFIED_MISTRAL_MODELS,
    VERIFIED_OPENHANDS_MODELS,
)
from openhands_cli.tui.settings.utils import organize_models_and_providers, get_supported_llm_models
from pydantic import SecretStr


class SettingsType(Enum):
    BASIC = 'basic'
    ADVANCED = 'advanced'


def settings_type_confirmation() -> tuple[UserConfirmation, SettingsType | None]:
    question = 'Which settings would you like to modify?'

    options =  [
        'LLM (Basic)',
        'Go back',
    ]

    index = cli_confirm(question, options)  # Blocking UI, not escapable


    if index == 0:
        return UserConfirmation.ACCEPT, SettingsType.BASIC

    return UserConfirmation.REJECT, None



def choose_llm_provider() -> str:
    question = '(Step 1/3) Select LLM Provider: '

    options = VERIFIED_PROVIDERS.copy()
    options.append('Select another provider')

    index = cli_confirm(question, options)
    if options[index] == 'Select another provider':
        # TODO: implement autocomplete for other provider selections
        followup_question = '(Step 1/3) Select LLM Provider (TAB for options, CTRL-c to cancel): '
        response, _ = prompt_user(followup_question, escapable=False)
        return response


    return options[index]



def _provider_models(provider: str) -> list[str]:
    if provider == 'openai':
        return VERIFIED_OPENAI_MODELS
    if provider == 'anthropic':
        return VERIFIED_ANTHROPIC_MODELS
    if provider == 'mistral':
        return VERIFIED_MISTRAL_MODELS
    if provider == 'openhands':
        return VERIFIED_OPENHANDS_MODELS
    return []


def choose_llm_model(provider: str) -> tuple[str | None, bool]:
    """Return (model, deferred). Uses fuzzy completer. Includes 'Select another model'."""
    # Build models list
    supported = organize_models_and_providers(get_supported_llm_models())

    if provider == 'openhands':
        models = VERIFIED_OPENHANDS_MODELS
        sep = '/'
    else:
        pi = supported.get(provider)
        if not pi:
            # Unknown provider: show flat list of models tagged for provider, else empty
            models = []
            sep = '/'
        else:
            models = pi.models
            sep = pi.separator

    # Default choice: prefer verified model if present; else first available
    verified = set(_provider_models(provider))
    default_model = None
    for m in models:
        if m in verified:
            default_model = m
            break
    if default_model is None and models:
        default_model = models[0]

    choices = list(models)
    choices.append('Select another model')

    question = '(Step 2/3) Select LLM Model (TAB for options, CTRL-c to cancel): '
    idx = cli_confirm(question, [*(choices)])
    selected = choices[idx]
    if selected == 'Select another model':
        resp, deferred = prompt_with_completer(
            '(Step 2/3) Type model id (TAB to complete, CTRL-c to cancel): ',
            models,
        )
        if deferred:
            return None, True
        # Allow user to paste provider/model; normalize to model id part
        if '/' in resp:
            resp = resp.split('/')[-1]
        if '.' in resp and provider != 'anthropic':
            # keep as-is; dot may be part of version
            pass
        return resp, False
    return selected, False



def _provider_models(provider: str) -> list[str]:
    if provider == 'openai':
        return VERIFIED_OPENAI_MODELS
    if provider == 'anthropic':
        return VERIFIED_ANTHROPIC_MODELS
    if provider == 'mistral':
        return VERIFIED_MISTRAL_MODELS
    if provider == 'openhands':
        return VERIFIED_OPENHANDS_MODELS
    return []


def choose_llm_model(provider: str) -> tuple[str | None, bool]:
    """Return (model, deferred). Uses fuzzy completer. Includes 'Select another model'."""
    # Build models list
    supported = organize_models_and_providers(get_supported_llm_models())

    if provider == 'openhands':
        models = VERIFIED_OPENHANDS_MODELS
        sep = '/'
    else:
        pi = supported.get(provider)
        if not pi:
            # Unknown provider: show flat list of models tagged for provider, else empty
            models = []
            sep = '/'
        else:
            models = pi.models
            sep = pi.separator

    # Default choice: prefer verified model if present; else first available
    verified = set(_provider_models(provider))
    default_model = None
    for m in models:
        if m in verified:
            default_model = m
            break
    if default_model is None and models:
        default_model = models[0]

    choices = list(models)
    choices.append('Select another model')

    question = '(Step 2/3) Select LLM Model (TAB for options, CTRL-c to cancel): '
    idx = cli_confirm(question, [*(choices)])
    selected = choices[idx]
    if selected == 'Select another model':
        resp, deferred = prompt_with_completer(
            '(Step 2/3) Type model id (TAB to complete, CTRL-c to cancel): ',
            models,
        )
        if deferred:
            return None, True
        # Allow user to paste provider/model; normalize to model id part
        if '/' in resp:
            resp = resp.split('/')[-1]
        if '.' in resp and provider != 'anthropic':
            # keep as-is; dot may be part of version
            pass
        return resp, False
    return selected, False

def _provider_models(provider: str) -> list[str]:
    if provider == 'openai':
        return VERIFIED_OPENAI_MODELS
    if provider == 'anthropic':
        return VERIFIED_ANTHROPIC_MODELS
    if provider == 'mistral':
        return VERIFIED_MISTRAL_MODELS
    if provider == 'openhands':
        return VERIFIED_OPENHANDS_MODELS
    return []


def choose_llm_model(provider: str) -> tuple[str | None, bool]:
    """Return (model, deferred). Uses fuzzy completer. Includes 'Select another model'."""
    # Build models list
    supported = organize_models_and_providers(get_supported_llm_models())

    if provider == 'openhands':
        models = VERIFIED_OPENHANDS_MODELS
        sep = '/'
    else:
        pi = supported.get(provider)
        if not pi:
            # Unknown provider: show flat list of models tagged for provider, else empty
            models = []
            sep = '/'
        else:
            models = pi.models
            sep = pi.separator

    # Default choice: prefer verified model if present; else first available
    verified = set(_provider_models(provider))
    default_model = None
    for m in models:
        if m in verified:
            default_model = m
            break
    if default_model is None and models:
        default_model = models[0]

    choices = models[0:4]
    choices.append('Select another model')

    question = '(Step 2/3) Select LLM Model (TAB for options, CTRL-c to cancel): '
    idx = cli_confirm(question, [*(choices)])
    selected = choices[idx]
    if selected == 'Select another model':
        resp, deferred = prompt_with_completer(
            '(Step 2/3) Type model id (TAB to complete, CTRL-c to cancel): ',
            models,
        )
        if deferred:
            return None, True
        # Allow user to paste provider/model; normalize to model id part
        if '/' in resp:
            resp = resp.split('/')[-1]
        if '.' in resp and provider != 'anthropic':
            # keep as-is; dot may be part of version
            pass
        return resp, False
    return selected, False

def specify_api_key(existing_api_key: SecretStr | None) -> str | None:
    if existing_api_key:
        question = f'(Step 3/3) Enter API Key [{existing_api_key.get_secret_value()[0:3]}***] (CTRL-c to cancel, ENTER to keep current, type new to change): '
    else:

        question = '(Step 3/3) Enter API Key (CTRL-c to cancel): '

    response, defer = prompt_user(question)
    if defer:
        return None

    return response


def save_settings_confirmation():
    question = 'Save new settings? (They will take effect after restart)'
    options = [
        'Yes, save',
        'No, discard'
    ]

    index = cli_confirm(question, options)
    options_mapping = {
        0: UserConfirmation.ACCEPT,
        1: UserConfirmation.REJECT,
    }
    return options_mapping.get(index, UserConfirmation.REJECT)

