from __future__ import annotations

from pydantic import (
    BaseModel,
    Field,
    SecretStr,
    SerializationInfo,
    field_serializer,
    model_validator,
)
from pydantic.json import pydantic_encoder

from openhands.core.config.config_utils import OH_MAX_ITERATIONS
from openhands.core.config.llm_config import LLMConfig
from openhands.core.config.utils import load_app_config
from openhands.integrations.provider import SecretStore


class Settings(BaseModel):
    """
    Persisted settings for OpenHands sessions
    """

    language: str = 'en'
    agent: str = 'CodeActAgent'
    max_iterations: int = OH_MAX_ITERATIONS
    security_analyzer: str = ''
    confirmation_mode: bool = False
    llm_model: str = 'anthropic/claude-3-5-sonnet-20241022'
    llm_api_key: SecretStr = SecretStr('')
    llm_base_url: str = ''
    remote_runtime_resource_factor: int = 1
    secrets_store: SecretStore = Field(default_factory=SecretStore, frozen=True)
    enable_default_condenser: bool = True
    enable_sound_notifications: bool = False
    user_consents_to_analytics: bool = False
    sandbox_base_container_image: str = ''
    sandbox_runtime_container_image: str = ''

    model_config = {
        'validate_assignment': True,
    }

    @field_serializer('llm_api_key')
    def llm_api_key_serializer(self, llm_api_key: SecretStr, info: SerializationInfo):
        """Custom serializer for the LLM API key.

        To serialize the API key instead of ********, set expose_secrets to True in the serialization context.
        """
        context = info.context
        if context and context.get('expose_secrets', False):
            return llm_api_key.get_secret_value()

        return pydantic_encoder(llm_api_key) if llm_api_key else None

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

        data['secrets_store'] = SecretStore(provider_tokens=tokens)
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
