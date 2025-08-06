from dataclasses import dataclass

from fastapi import Request
from pydantic import SecretStr

from openhands.core.config import ConfigurationMerger, OpenHandsConfig
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
        """Get user settings with proper precedence handling.

        This method retrieves user settings from the settings store and applies the correct
        precedence order:
        1. Command-line arguments (already in OpenHandsConfig)
        2. User settings (from settings store)
        3. Environment variables (already in OpenHandsConfig)
        4. TOML files (already in OpenHandsConfig)
        5. Default values (already in OpenHandsConfig)

        For MCP configuration, we merge the lists from both sources.

        Returns:
            The merged settings, or None if no settings exist.
        """
        # Return cached settings if available
        settings = self._settings
        if settings:
            return settings

        # Load settings from store
        settings_store = await self.get_user_settings_store()
        settings = await settings_store.load()

        # If no settings exist, return None
        if not settings:
            self._settings = None
            return None

        # Load config (contains command-line args, env vars, and TOML settings)
        config = OpenHandsConfig()
        
        # Start with a new settings object
        final_settings = Settings(
            language=settings.language,
            agent=settings.agent,
            max_iterations=settings.max_iterations,
            security_analyzer=settings.security_analyzer,
            confirmation_mode=settings.confirmation_mode,
            llm_model=settings.llm_model,
            llm_api_key=settings.llm_api_key,
            llm_base_url=settings.llm_base_url,
            remote_runtime_resource_factor=settings.remote_runtime_resource_factor,
            sandbox_base_container_image=settings.sandbox_base_container_image,
            sandbox_runtime_container_image=settings.sandbox_runtime_container_image,
            sandbox_api_key=settings.sandbox_api_key,
            mcp_config=settings.mcp_config,
            search_api_key=settings.search_api_key,
            max_budget_per_task=settings.max_budget_per_task,
            git_user_name=settings.git_user_name,
            git_user_email=settings.git_user_email,
        )
        
        # Apply command-line values with highest precedence
        for settings_field, config_field, nested_obj in ConfigurationMerger.FIELD_MAPPING:
            # Get the value from the command-line config
            if nested_obj is None:
                cmd_value = getattr(config, config_field, None)
            elif nested_obj == 'llm_config':
                cmd_value = getattr(config.get_llm_config(), config_field, None)
            elif nested_obj == 'security':
                cmd_value = getattr(config.security, config_field, None)
            elif nested_obj == 'sandbox':
                cmd_value = getattr(config.sandbox, config_field, None)
            else:
                cmd_value = None
                
            # Skip if the command-line value is None
            if cmd_value is None:
                continue
                
            # Apply the command-line value to the final settings
            if settings_field == 'llm_api_key' and isinstance(cmd_value, str):
                # Convert string API keys to SecretStr
                setattr(final_settings, settings_field, SecretStr(cmd_value))
            elif settings_field == 'sandbox_api_key' and isinstance(cmd_value, str):
                # Convert string API keys to SecretStr
                setattr(final_settings, settings_field, SecretStr(cmd_value))
            elif settings_field == 'search_api_key' and isinstance(cmd_value, str):
                # Convert string API keys to SecretStr
                setattr(final_settings, settings_field, SecretStr(cmd_value))
            else:
                # Apply the value directly
                setattr(final_settings, settings_field, cmd_value)
        
        # Special handling for MCP config - merge the lists
        if config.mcp is not None:
            if final_settings.mcp_config is None:
                final_settings.mcp_config = config.mcp
            else:
                # Create a new MCP config with both server lists
                final_mcp = MCPConfig()
                
                # Add config servers first (highest precedence)
                if config.mcp.sse_servers:
                    final_mcp.sse_servers = list(config.mcp.sse_servers)
                
                # Then add user settings servers
                if final_settings.mcp_config.sse_servers:
                    if not final_mcp.sse_servers:
                        final_mcp.sse_servers = []
                    final_mcp.sse_servers.extend(final_settings.mcp_config.sse_servers)
                
                # Do the same for stdio and shttp servers
                if config.mcp.stdio_servers:
                    final_mcp.stdio_servers = list(config.mcp.stdio_servers)
                if final_settings.mcp_config.stdio_servers:
                    if not final_mcp.stdio_servers:
                        final_mcp.stdio_servers = []
                    final_mcp.stdio_servers.extend(final_settings.mcp_config.stdio_servers)
                
                if config.mcp.shttp_servers:
                    final_mcp.shttp_servers = list(config.mcp.shttp_servers)
                if final_settings.mcp_config.shttp_servers:
                    if not final_mcp.shttp_servers:
                        final_mcp.shttp_servers = []
                    final_mcp.shttp_servers.extend(final_settings.mcp_config.shttp_servers)
                
                # Set the final MCP config
                final_settings.mcp_config = final_mcp

        # Cache and return settings
        self._settings = final_settings
        return final_settings

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
