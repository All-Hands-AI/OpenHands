from __future__ import annotations

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    SecretStr,
    SerializationInfo,
    field_serializer,
    model_validator,
)
from pydantic.json import pydantic_encoder

from openhands.core.config.llm_config import LLMConfig
from openhands.core.config.mcp_config import MCPConfig
from openhands.core.config.utils import load_openhands_config
from openhands.storage.data_models.user_secrets import UserSecrets


class Settings(BaseModel):
    """Persisted settings for OpenHands sessions."""

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
    user_consents_to_analytics: bool | None = None
    sandbox_base_container_image: str | None = None
    sandbox_runtime_container_image: str | None = None
    mcp_config: MCPConfig | None = None
    search_api_key: SecretStr | None = None
    sandbox_api_key: SecretStr | None = None
    max_budget_per_task: float | None = None
    email: str | None = None
    temperature: float = Field(default=0.0)
    top_p: float = Field(default=1.0)
    max_output_tokens: int | None = None
    max_input_tokens: int | None = None
    max_message_chars: int = Field(default=30_000)
    input_cost_per_token: float | None = None
    output_cost_per_token: float | None = None
    email_verified: bool | None = None

    # Agent Configuration Parameters
    enable_browsing: bool = Field(default=True)
    enable_llm_editor: bool = Field(default=False)
    enable_editor: bool = Field(default=True)
    enable_jupyter: bool = Field(default=True)
    enable_cmd: bool = Field(default=True)
    enable_think: bool = Field(default=True)
    enable_finish: bool = Field(default=True)
    enable_prompt_extensions: bool = Field(default=True)
    disabled_microagents: list[str] = Field(default_factory=list)
    enable_history_truncation: bool = Field(default=True)

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

        context = info.context
        if context and context.get('expose_secrets', False):
            return api_key.get_secret_value()

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
            converted_store = UserSecrets(provider_tokens=tokens)
            secret_store = secret_store.model_copy(
                update={'provider_tokens': converted_store.provider_tokens}
            )
        else:
            secret_store.model_copy(update={'provider_tokens': tokens})

        if isinstance(custom_secrets, dict):
            converted_store = UserSecrets(custom_secrets=custom_secrets)
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
    def secrets_store_serializer(self, secrets: UserSecrets, info: SerializationInfo):
        """Custom serializer for secrets store."""
        """Force invalidate secret store"""
        return {'provider_tokens': {}}

    @staticmethod
    def from_config() -> Settings | None:
        app_config = load_openhands_config()
        llm_config: LLMConfig = app_config.get_llm_config()
        if llm_config.api_key is None:
            # If no api key has been set, we take this to mean that there is no reasonable default
            return None
        security = app_config.security

        # Get MCP config if available
        mcp_config = None
        if hasattr(app_config, 'mcp'):
            mcp_config = app_config.mcp

        # Get agent config for the default agent
        agent_config = app_config.get_agent_config(app_config.default_agent)

        settings = Settings(
            language='en',
            agent=app_config.default_agent,
            max_iterations=app_config.max_iterations,
            security_analyzer=security.security_analyzer,
            confirmation_mode=security.confirmation_mode,
            llm_model=llm_config.model,
            llm_api_key=llm_config.api_key,
            llm_base_url=llm_config.base_url,
            temperature=llm_config.temperature,
            top_p=llm_config.top_p,
            max_output_tokens=llm_config.max_output_tokens,
            max_input_tokens=llm_config.max_input_tokens,
            max_message_chars=llm_config.max_message_chars,
            input_cost_per_token=llm_config.input_cost_per_token,
            output_cost_per_token=llm_config.output_cost_per_token,
            remote_runtime_resource_factor=app_config.sandbox.remote_runtime_resource_factor,
            mcp_config=mcp_config,
            search_api_key=app_config.search_api_key,
            max_budget_per_task=app_config.max_budget_per_task,
            # Agent configuration parameters
            enable_browsing=agent_config.enable_browsing,
            enable_llm_editor=agent_config.enable_llm_editor,
            enable_editor=agent_config.enable_editor,
            enable_jupyter=agent_config.enable_jupyter,
            enable_cmd=agent_config.enable_cmd,
            enable_think=agent_config.enable_think,
            enable_finish=agent_config.enable_finish,
            enable_prompt_extensions=agent_config.enable_prompt_extensions,
            disabled_microagents=agent_config.disabled_microagents,
            enable_history_truncation=agent_config.enable_history_truncation,
        )
        return settings
