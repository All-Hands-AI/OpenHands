from __future__ import annotations

from pydantic import (
    BaseModel,
    SecretStr,
)

from openhands.integrations.service_types import ProviderType
from openhands.storage.data_models.settings import Settings


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

    provider_tokens_set: dict[ProviderType, str | None] | None = (
        None  # provider + base_domain key-value pair
    )
    llm_api_key_set: bool


class GETSettingsCustomSecrets(BaseModel):
    """
    Custom secrets names
    """

    custom_secrets: list[str] | None = None
