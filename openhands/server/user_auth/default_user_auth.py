from dataclasses import dataclass

from fastapi import Request
from pydantic import SecretStr

from openhands.core.config.mcp_config import MCPConfig
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
        settings = self._settings
        if settings:
            return settings
        settings_store = await self.get_user_settings_store()
        settings = await settings_store.load()

        # Merge config.toml settings with stored settings
        if settings:
            settings = self._merge_with_config_settings(settings)

        self._settings = settings
        return settings

    def _merge_with_config_settings(self, settings: Settings) -> Settings:
        """Merge config.toml settings with stored settings.

        Config.toml takes priority for MCP settings, but they are merged rather than replaced.
        """
        # Get config.toml settings
        config_settings = Settings.from_config()
        if not config_settings or not config_settings.mcp_config:
            return settings

        # If stored settings don't have MCP config, use config.toml MCP config
        if not settings.mcp_config:
            settings.mcp_config = config_settings.mcp_config
            return settings

        # Both have MCP config - merge them with config.toml taking priority
        merged_mcp = MCPConfig(
            sse_servers=list(config_settings.mcp_config.sse_servers)
            + list(settings.mcp_config.sse_servers),
            stdio_servers=list(config_settings.mcp_config.stdio_servers)
            + list(settings.mcp_config.stdio_servers),
            shttp_servers=list(config_settings.mcp_config.shttp_servers)
            + list(settings.mcp_config.shttp_servers),
        )

        # Create new settings with merged MCP config
        settings.mcp_config = merged_mcp
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
