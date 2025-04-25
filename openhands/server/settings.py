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

from openhands.core.config.llm_config import LLMConfig
from openhands.core.config.utils import load_app_config
from openhands.integrations.provider import SecretStore


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
    secrets_store: SecretStore = Field(default_factory=SecretStore, frozen=True)
    enable_default_condenser: bool = True
    enable_sound_notifications: bool = False
    user_consents_to_analytics: bool | None = None
    sandbox_base_container_image: str | None = None
    sandbox_runtime_container_image: str | None = None

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

        custom_secrets = secrets_store.get('custom_secrets')
        tokens = secrets_store.get('provider_tokens')

        secret_store = SecretStore(provider_tokens={}, custom_secrets={})

        if isinstance(tokens, dict):
            converted_store = SecretStore(provider_tokens=tokens)
            secret_store = secret_store.model_copy(
                update={'provider_tokens': converted_store.provider_tokens}
            )
        else:
            secret_store.model_copy(update={'provider_tokens': tokens})

        if isinstance(custom_secrets, dict):
            converted_store = SecretStore(custom_secrets=custom_secrets)
            secret_store = secret_store.model_copy(
                update={'custom_secrets': converted_store.custom_secrets}
            )
        else:
            secret_store = secret_store.model_copy(
                update={'custom_secrets': custom_secrets}
            )
        data['secret_store'] = secret_store
        return data

    @field_serializer('secrets_store')
    def secrets_store_serializer(self, secrets: SecretStore, info: SerializationInfo):
        """Custom serializer for secrets store."""
        return {
            'provider_tokens': secrets.provider_tokens_serializer(
                secrets.provider_tokens, info
            ),
            'custom_secrets': secrets.custom_secrets_serializer(
                secrets.custom_secrets, info
            ),
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
        )
        return settings


class POSTSettingsModel(Settings):
    """
    Settings for POST requests
    """

    provider_tokens: dict[str, str] = {}


class POSTSettingsCustomSecrets(BaseModel):
    """
    Adding new custom secret
    """

    custom_secrets: dict[str, str | SecretStr] = {}


class GETSettingsModel(Settings):
    """
    Settings with additional token data for the frontend
    """

    provider_tokens_set: dict[str, bool] | None = None
    llm_api_key_set: bool


class GETSettingsCustomSecrets(BaseModel):
    """
    Custom secrets names
    """

    custom_secrets: list[str] | None = None
