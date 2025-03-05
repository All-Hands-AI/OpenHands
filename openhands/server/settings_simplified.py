from __future__ import annotations

from pydantic import BaseModel, SecretStr, SerializationInfo, field_serializer, model_validator
from pydantic.json import pydantic_encoder

from openhands.core.config.llm_config import LLMConfig
from openhands.core.config.utils import load_app_config
from openhands.integrations.provider_simplified import ProviderToken, ProviderType, SecretStore

class Settings(BaseModel):
    """Persisted settings for OpenHands sessions"""
    language: str | None = None
    agent: str | None = None
    max_iterations: int | None = None
    security_analyzer: str | None = None
    confirmation_mode: bool | None = None
    llm_model: str | None = None
    llm_api_key: SecretStr | None = None
    llm_base_url: str | None = None
    remote_runtime_resource_factor: int | None = None
    secrets_store: SecretStore = SecretStore()
    enable_default_condenser: bool = False
    enable_sound_notifications: bool = False
    user_consents_to_analytics: bool | None = None

    @field_serializer('llm_api_key')
    def llm_api_key_serializer(self, llm_api_key: SecretStr, info: SerializationInfo):
        """Custom serializer for the LLM API key."""
        if not llm_api_key:
            return None
        context = info.context
        if context and context.get('expose_secrets', False):
            return llm_api_key.get_secret_value()
        return pydantic_encoder(llm_api_key)

    @model_validator(mode='before')
    @classmethod
    def convert_provider_tokens(cls, data: dict) -> dict:
        """Convert provider tokens from JSON format to SecretStore format."""
        if not isinstance(data, dict):
            return data

        # Handle root-level provider_tokens (backward compatibility)
        if 'provider_tokens' in data and not data.get('secrets_store'):
            tokens = data.pop('provider_tokens')
            if isinstance(tokens, dict):
                data['secrets_store'] = {'provider_tokens': tokens}

        # Convert string tokens to ProviderToken objects
        if 'secrets_store' in data and isinstance(data['secrets_store'], dict):
            tokens = data['secrets_store'].get('provider_tokens', {})
            if isinstance(tokens, dict):
                converted = {}
                for type_str, value in tokens.items():
                    try:
                        provider = ProviderType(type_str)
                        if isinstance(value, str) and value:
                            converted[provider] = ProviderToken(token=SecretStr(value))
                        elif isinstance(value, dict) and value.get('token'):
                            converted[provider] = ProviderToken(
                                token=SecretStr(value['token']),
                                user_id=value.get('user_id')
                            )
                    except ValueError:
                        continue
                data['secrets_store']['provider_tokens'] = converted

        return data

    @staticmethod
    def from_config() -> Settings | None:
        app_config = load_app_config()
        llm_config: LLMConfig = app_config.get_llm_config()
        if llm_config.api_key is None:
            return None
        security = app_config.security
        return Settings(
            language='en',
            agent=app_config.default_agent,
            max_iterations=app_config.max_iterations,
            security_analyzer=security.security_analyzer,
            confirmation_mode=security.confirmation_mode,
            llm_model=llm_config.model,
            llm_api_key=llm_config.api_key,
            llm_base_url=llm_config.base_url,
            remote_runtime_resource_factor=app_config.sandbox.remote_runtime_resource_factor,
        )

class POSTSettingsModel(Settings):
    """Settings for POST requests"""
    unset_token: bool | None = None
    provider_tokens: dict[str, str] = {}  # Accept string tokens from frontend

class GETSettingsModel(Settings):
    """Settings with additional token data for the frontend"""
    token_is_set: bool | None = None