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

        # Create a new settings object with the same values
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

        # Apply command-line arguments with highest precedence
        # Only override if the config has a non-None value
        if config.default_agent is not None:
            final_settings.agent = config.default_agent

        if config.max_iterations is not None:
            final_settings.max_iterations = config.max_iterations

        # Handle other config fields that might be set via command line
        if config.git_user_name is not None:
            final_settings.git_user_name = config.git_user_name

        if config.git_user_email is not None:
            final_settings.git_user_email = config.git_user_email

        if config.max_budget_per_task is not None:
            final_settings.max_budget_per_task = config.max_budget_per_task

        # Handle LLM config
        llm_config = config.get_llm_config()
        if llm_config.model is not None:
            final_settings.llm_model = llm_config.model

        if llm_config.api_key is not None:
            # Convert to SecretStr if needed
            if isinstance(llm_config.api_key, str):
                final_settings.llm_api_key = SecretStr(llm_config.api_key)
            elif hasattr(llm_config.api_key, 'get_secret_value'):
                final_settings.llm_api_key = llm_config.api_key

        if llm_config.base_url is not None:
            final_settings.llm_base_url = llm_config.base_url

        # Handle security config
        if config.security.security_analyzer is not None:
            final_settings.security_analyzer = config.security.security_analyzer

        if config.security.confirmation_mode is not None:
            final_settings.confirmation_mode = config.security.confirmation_mode

        # Handle sandbox config
        if config.sandbox.remote_runtime_resource_factor is not None:
            final_settings.remote_runtime_resource_factor = config.sandbox.remote_runtime_resource_factor

        if config.sandbox.base_container_image is not None:
            final_settings.sandbox_base_container_image = config.sandbox.base_container_image

        if config.sandbox.runtime_container_image is not None:
            final_settings.sandbox_runtime_container_image = config.sandbox.runtime_container_image

        # Special handling for MCP config - merge the lists
        if config.mcp is not None:
            # Get user settings MCP config
            user_mcp_config = settings.mcp_config

            # Create a new MCP config with both server lists
            final_mcp = MCPConfig()

            # Add config servers first (highest precedence)
            if config.mcp.sse_servers:
                final_mcp.sse_servers = list(config.mcp.sse_servers)

            # Then add user settings servers
            if user_mcp_config and user_mcp_config.sse_servers:
                if not final_mcp.sse_servers:
                    final_mcp.sse_servers = []
                final_mcp.sse_servers.extend(user_mcp_config.sse_servers)

            # Do the same for stdio and shttp servers
            if config.mcp.stdio_servers:
                final_mcp.stdio_servers = list(config.mcp.stdio_servers)
            if user_mcp_config and user_mcp_config.stdio_servers:
                if not final_mcp.stdio_servers:
                    final_mcp.stdio_servers = []
                final_mcp.stdio_servers.extend(user_mcp_config.stdio_servers)

            if config.mcp.shttp_servers:
                final_mcp.shttp_servers = list(config.mcp.shttp_servers)
            if user_mcp_config and user_mcp_config.shttp_servers:
                if not final_mcp.shttp_servers:
                    final_mcp.shttp_servers = []
                final_mcp.shttp_servers.extend(user_mcp_config.shttp_servers)

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
