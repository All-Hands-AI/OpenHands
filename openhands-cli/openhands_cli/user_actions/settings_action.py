from enum import Enum

from pydantic import SecretStr

from openhands_cli.user_actions.types import UserConfirmation
from openhands_cli.user_actions.prompt_handler import PromptHandler
from openhands_cli.user_actions.settings_specs import (
    SETTINGS_TYPE_SPEC,
    SAVE_SETTINGS_SPEC,
    create_llm_provider_spec,
    create_llm_model_spec,
    create_llm_model_autocomplete_spec,
    create_api_key_spec,
    PROVIDER_AUTOCOMPLETE_SPEC,
)
from openhands_cli.tui.settings.constants import (
    VERIFIED_OPENAI_MODELS,
    VERIFIED_ANTHROPIC_MODELS,
    VERIFIED_MISTRAL_MODELS,
    VERIFIED_OPENHANDS_MODELS,
)
from openhands_cli.tui.settings.utils import organize_models_and_providers, get_supported_llm_models


class SettingsType(Enum):
    BASIC = 'basic'
    ADVANCED = 'advanced'


def settings_type_confirmation() -> tuple[UserConfirmation, SettingsType | None]:
    """Prompt user to select settings type using spec-driven approach."""
    prompt_handler = PromptHandler()
    result = prompt_handler.execute_prompt(SETTINGS_TYPE_SPEC)
    
    if result.confirmation == UserConfirmation.ACCEPT and result.selected_index == 0:
        return UserConfirmation.ACCEPT, SettingsType.BASIC
    
    return UserConfirmation.REJECT, None


def choose_llm_provider() -> str:
    """Choose LLM provider using spec-driven approach."""
    prompt_handler = PromptHandler()
    
    # First prompt: select from verified providers or "Select another provider"
    provider_spec = create_llm_provider_spec()
    result = prompt_handler.execute_prompt(provider_spec)
    
    if result.value == "Select another provider":
        # Follow-up prompt for custom provider
        custom_result = prompt_handler.execute_prompt(PROVIDER_AUTOCOMPLETE_SPEC)
        return custom_result.value or ""
    
    return result.value or ""


def choose_llm_model(provider: str) -> tuple[str | None, bool]:
    """Choose LLM model using spec-driven approach. Return (model, deferred)."""
    prompt_handler = PromptHandler()
    
    # Build models list
    supported = organize_models_and_providers(get_supported_llm_models())

    if provider == 'openhands':
        models = VERIFIED_OPENHANDS_MODELS
    else:
        pi = supported.get(provider)
        if not pi:
            models = []
        else:
            models = pi.models

    # First prompt: select from top models or "Select another model"
    model_spec = create_llm_model_spec(models)
    result = prompt_handler.execute_prompt(model_spec)
    
    if result.confirmation != UserConfirmation.ACCEPT:
        return None, True
    
    if result.value == "Select another model":
        # Follow-up prompt with autocomplete
        autocomplete_spec = create_llm_model_autocomplete_spec(models)
        autocomplete_result = prompt_handler.execute_prompt(autocomplete_spec)
        
        if autocomplete_result.confirmation != UserConfirmation.ACCEPT:
            return None, True
        
        resp = autocomplete_result.value or ""
        # Allow user to paste provider/model; normalize to model id part
        if '/' in resp:
            resp = resp.split('/')[-1]
        if '.' in resp and provider != 'anthropic':
            # keep as-is; dot may be part of version
            pass
        return resp, False
    
    return result.value, False


def _provider_models(provider: str) -> list[str]:
    """Get verified models for a provider."""
    if provider == 'openai':
        return VERIFIED_OPENAI_MODELS
    if provider == 'anthropic':
        return VERIFIED_ANTHROPIC_MODELS
    if provider == 'mistral':
        return VERIFIED_MISTRAL_MODELS
    if provider == 'openhands':
        return VERIFIED_OPENHANDS_MODELS
    return []


def prompt_api_key(existing_api_key: SecretStr | None = None) -> tuple[str | None, bool]:
    """Prompt for API key using spec-driven approach. Return (api_key, deferred)."""
    prompt_handler = PromptHandler()
    
    api_key_spec = create_api_key_spec(existing_api_key)
    result = prompt_handler.execute_prompt(api_key_spec)
    
    if result.confirmation != UserConfirmation.ACCEPT:
        return None, True
    
    return result.value, False


def save_settings_confirmation() -> bool:
    """Prompt user to confirm saving settings."""
    prompt_handler = PromptHandler()
    result = prompt_handler.execute_prompt(SAVE_SETTINGS_SPEC)
    
    return result.confirmation == UserConfirmation.ACCEPT and result.selected_index == 0