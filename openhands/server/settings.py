from __future__ import annotations

from pydantic import (
    BaseModel,
    SecretStr,
)

from openhands.core.config.mcp_config import MCPConfig
from openhands.integrations.provider import ProviderToken
from openhands.integrations.service_types import ProviderType
from openhands.storage.data_models.settings import Settings


class POSTProviderModel(BaseModel):
    """
    Settings for POST requests
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
    enable_default_condenser: bool = True
    enable_sound_notifications: bool = False
    user_consents_to_analytics: bool | None = None
    sandbox_base_container_image: str | None = None
    sandbox_runtime_container_image: str | None = None
    mcp_config: MCPConfig | None = None
    provider_tokens: dict[ProviderType, ProviderToken] = {}


class POSTCustomSecrets(BaseModel):
    """
    Adding new custom secret
    """

    custom_secrets: dict[str, str | SecretStr] = {}


class GETSettingsModel(Settings):
    """
    Settings with additional token data for the frontend
    """

    provider_tokens_set: dict[ProviderType, str | None] | None = (
        None  # provider + base_domain key-value pair
    )
    llm_api_key_set: bool


class GETCustomSecrets(BaseModel):
    """
    Custom secrets names
    """

    custom_secrets: list[str] | None = None
