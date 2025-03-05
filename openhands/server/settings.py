from __future__ import annotations

from pydantic import (
    BaseModel,
    SecretStr,
    SerializationInfo,
    field_serializer,
    model_validator,
)
from pydantic.json import pydantic_encoder

from openhands.core.config.llm_config import LLMConfig
from openhands.core.config.utils import load_app_config
from openhands.integrations.provider import ProviderToken, ProviderType, SecretStore


class Settings(BaseModel):
    """
    Persisted settings for OpenHands sessions
    """

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
        """Custom serializer for the LLM API key.

        To serialize the API key instead of ********, set expose_secrets to True in the serialization context.
        """
        context = info.context
        if context and context.get('expose_secrets', False):
            return llm_api_key.get_secret_value()

        return pydantic_encoder(llm_api_key)

    @staticmethod
    def _convert_token_value(
        token_type: ProviderType, token_value: str | dict
    ) -> ProviderToken | None:
        """Convert a token value to a ProviderToken object."""
        if isinstance(token_value, dict):
            token_str = token_value.get('token')
            if not token_str:
                return None
            return ProviderToken(
                token=SecretStr(token_str),
                user_id=token_value.get('user_id'),
            )
        if isinstance(token_value, str) and token_value:
            return ProviderToken(token=SecretStr(token_value), user_id=None)
        return None

    @model_validator(mode='before')
    @classmethod
    def convert_provider_tokens(cls, data: dict | object) -> dict | object:
        """Convert provider tokens from JSON format to SecretStore format."""
        if not isinstance(data, dict):
            return data

        secrets_store = data.get('secrets_store')
        if not isinstance(secrets_store, dict):
            return data

        tokens = secrets_store.get('provider_tokens')
        if not isinstance(tokens, dict):
            return data

        converted_tokens = {}
        for token_type_str, token_value in tokens.items():
            if not token_value:
                continue

            try:
                token_type = ProviderType(token_type_str)
            except ValueError:
                continue

            provider_token = cls._convert_token_value(token_type, token_value)
            if provider_token:
                converted_tokens[token_type] = provider_token

        data['secrets_store'] = SecretStore(provider_tokens=converted_tokens)
        return data

    @field_serializer('secrets_store')
    def secrets_store_serializer(self, secrets: SecretStore, info: SerializationInfo):
        """Custom serializer for secrets store."""
        return {
            'provider_tokens': secrets.provider_tokens_serializer(
                secrets.provider_tokens, info
            )
        }

    @staticmethod
    def from_config() -> Settings | None:
        app_config = load_app_config()
        llm_config: LLMConfig = app_config.get_llm_config()
        if llm_config.api_key is None:
            # If no api key has been set, we take this to mean that there is no reasonable default
            return None
        security = app_config.security
        settings = Settings(
            language='en',
            agent=app_config.default_agent,
            max_iterations=app_config.max_iterations,
            security_analyzer=security.security_analyzer,
            confirmation_mode=security.confirmation_mode,
            llm_model=llm_config.model,
            llm_api_key=llm_config.api_key,
            llm_base_url=llm_config.base_url,
            remote_runtime_resource_factor=app_config.sandbox.remote_runtime_resource_factor,
            provider_tokens={},
        )
        return settings


class POSTSettingsModel(Settings):
    """
    Settings for POST requests
    """

    unset_github_token: bool | None = None
    # Override provider_tokens to accept string tokens from frontend
    provider_tokens: dict[str, str] = {}

    @field_serializer('provider_tokens')
    def provider_tokens_serializer(self, provider_tokens: dict[str, str]):
        return provider_tokens


class GETSettingsModel(Settings):
    """
    Settings with additional token data for the frontend
    """

    github_token_is_set: bool | None = None
