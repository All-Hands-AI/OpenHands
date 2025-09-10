from __future__ import annotations

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    SecretStr,
    SerializationInfo,
    field_serializer,
    field_validator,
    model_validator,
)
from pydantic.json import pydantic_encoder

from .llm_config import LLMConfig
from .mcp_config import MCPConfig
from .user_secrets import UserSecrets


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
    # Planned to be removed from settings
    secrets_store: UserSecrets = Field(default_factory=UserSecrets, frozen=True)
    enable_default_condenser: bool = True
    enable_sound_notifications: bool = False
    enable_proactive_conversation_starters: bool = True
    enable_solvability_analysis: bool = True
    user_consents_to_analytics: bool | None = None
    sandbox_base_container_image: str | None = None
    sandbox_runtime_container_image: str | None = None
    mcp_config: MCPConfig | None = None
    search_api_key: SecretStr | None = None
    sandbox_api_key: SecretStr | None = None
    max_budget_per_task: float | None = None
    # Maximum number of events in the conversation view before condensation runs
    condenser_max_size: int | None = None
    email: str | None = None
    email_verified: bool | None = None
    git_user_name: str | None = None
    git_user_email: str | None = None

    model_config = ConfigDict(
        validate_assignment=True,
    )

    @field_serializer('llm_api_key', 'search_api_key')
    def api_key_serializer(self, api_key: SecretStr | None, info: SerializationInfo):
        """Custom serializer for API keys.

        To serialize the API key instead of ********, set expose_secrets to True in the serialization context.
        """
        if api_key is None:
            return None

        # Get the secret value to check if it's empty
        secret_value = api_key.get_secret_value()
        if not secret_value or not secret_value.strip():
            return None

        context = info.context
        if context and context.get('expose_secrets', False):
            return secret_value

        return pydantic_encoder(api_key)

    @model_validator(mode='before')
    @classmethod
    def convert_provider_tokens(cls, data: dict | object) -> dict | object:
        """Convert provider tokens from JSON format to UserSecrets format."""
        if not isinstance(data, dict):
            return data

        secrets_store = data.get('secrets_store')
        if not isinstance(secrets_store, dict):
            return data

        custom_secrets = secrets_store.get('custom_secrets')
        tokens = secrets_store.get('provider_tokens')

        secret_store = UserSecrets(provider_tokens={}, custom_secrets={})

        if isinstance(tokens, dict):
            secret_store = secret_store.model_copy(
                update={'provider_tokens': tokens}
            )

        if isinstance(custom_secrets, dict):
            secret_store = secret_store.model_copy(
                update={'custom_secrets': custom_secrets}
            )
        
        data['secrets_store'] = secret_store
        return data

    @field_validator('condenser_max_size')
    @classmethod
    def validate_condenser_max_size(cls, v: int | None) -> int | None:
        if v is None:
            return v
        if v < 20:
            raise ValueError('condenser_max_size must be at least 20')
        return v

    @field_serializer('secrets_store')
    def secrets_store_serializer(self, secrets: UserSecrets, info: SerializationInfo):
        """Custom serializer for secrets store."""
        """Force invalidate secret store"""
        return {'provider_tokens': {}}

    def merge_with_config_settings(self) -> 'Settings':
        """Merge config.toml settings with stored settings.

        Config.toml takes priority for MCP settings, but they are merged rather than replaced.
        This method can be used by both server mode and CLI mode.
        
        Note: This simplified version doesn't load from config files.
        """
        return self