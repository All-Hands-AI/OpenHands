from dataclasses import dataclass

from fastapi import Request
from pydantic import SecretStr

from openhands.core.config import ConfigurationMerger, OpenHandsConfig
from openhands.integrations.provider import PROVIDER_TOKEN_TYPE
from openhands.server import shared
from openhands.server.settings import Settings
from openhands.server.user_auth.user_auth import UserAuth
from openhands.storage.data_models.user_secrets import UserSecrets
from openhands.storage.secrets.secrets_store import SecretsStore
from openhands.storage.settings.settings_store import SettingsStore


@dataclass
class DefaultUserAuth(UserAuth):
    """Default user authentication mechanism"""

    _settings: Settings | None = None
    _settings_store: SettingsStore | None = None
    _secrets_store: SecretsStore | None = None
    _user_secrets: UserSecrets | None = None

    async def get_user_id(self) -> str | None:
        """The default implementation does not support multi tenancy, so user_id is always None"""
        return None

    async def get_user_email(self) -> str | None:
        """The default implementation does not support multi tenancy, so email is always None"""
        return None

    async def get_access_token(self) -> SecretStr | None:
        """The default implementation does not support multi tenancy, so access_token is always None"""
        return None

    async def get_user_settings_store(self) -> SettingsStore:
        settings_store = self._settings_store
        if settings_store:
            return settings_store
        user_id = await self.get_user_id()
        settings_store = await shared.SettingsStoreImpl.get_instance(
            shared.config, user_id
        )
        if settings_store is None:
            raise ValueError('Failed to get settings store instance')
        self._settings_store = settings_store
        return settings_store

    async def get_user_settings(self) -> Settings | None:
        """Get user settings, merging MCP config from config.toml if needed.

        This method retrieves user settings from the settings store. If settings exist,
        it merges the MCP configuration from config.toml with the user's settings.

        Returns:
            The user settings with merged MCP config, or None if no settings exist.
        """
        # Return cached settings if available
        settings = self._settings
        if settings:
            return settings

        # Load settings from store
        settings_store = await self.get_user_settings_store()
        settings = await settings_store.load()

        # If settings exist, merge MCP config from config.toml
        if settings:
            # Load default config
            config = OpenHandsConfig()

            # Only merge MCP settings if needed
            if config.mcp is not None:
                # Create merged config with settings taking precedence
                merged_config = ConfigurationMerger.merge_settings_with_config(
                    settings, config
                )

                # Update settings with merged MCP config
                if merged_config.mcp is not None:
                    settings.mcp_config = merged_config.mcp

        # Cache and return settings
        self._settings = settings
        return settings

    async def get_secrets_store(self) -> SecretsStore:
        secrets_store = self._secrets_store
        if secrets_store:
            return secrets_store
        user_id = await self.get_user_id()
        secret_store = await shared.SecretsStoreImpl.get_instance(
            shared.config, user_id
        )
        if secret_store is None:
            raise ValueError('Failed to get secrets store instance')
        self._secrets_store = secret_store
        return secret_store

    async def get_user_secrets(self) -> UserSecrets | None:
        user_secrets = self._user_secrets
        if user_secrets:
            return user_secrets
        secrets_store = await self.get_secrets_store()
        user_secrets = await secrets_store.load()
        self._user_secrets = user_secrets
        return user_secrets

    async def get_provider_tokens(self) -> PROVIDER_TOKEN_TYPE | None:
        user_secrets = await self.get_user_secrets()
        if user_secrets is None:
            return None
        return user_secrets.provider_tokens

    @classmethod
    async def get_instance(cls, request: Request) -> UserAuth:
        user_auth = DefaultUserAuth()
        return user_auth
