"""
Resolver User Context for enterprise integrations.

This module contains the ResolverUserContext class that provides user context
for resolver operations in enterprise integrations.
"""

from openhands.app_server.user.user_context import UserContext
from openhands.app_server.user.user_models import UserInfo
from openhands.integrations.provider import PROVIDER_TOKEN_TYPE
from openhands.integrations.service_types import ProviderType


class ResolverUserContext(UserContext):
    """User context for resolver operations that inherits from UserContext."""
    
    def __init__(self, keycloak_user_id: str, git_provider_tokens: PROVIDER_TOKEN_TYPE, custom_secrets=None):
        from server.config import get_config
        from storage.database import session_maker
        from storage.saas_secrets_store import SaasSecretsStore
        from storage.saas_settings_store import SaasSettingsStore

        self.keycloak_user_id = keycloak_user_id
        self.git_provider_tokens = git_provider_tokens
        self.custom_secrets = custom_secrets or {}
        self.settings_store = SaasSettingsStore(
            user_id=self.keycloak_user_id,
            session_maker=session_maker,
            config=get_config(),
        )

        self.secrets_store = SaasSecretsStore(
            self.keycloak_user_id, session_maker, get_config()
        )

    async def get_user_id(self) -> str | None:
        return self.keycloak_user_id

    async def get_user_info(self) -> UserInfo:
        user_settings = await self.settings_store.load()
        return UserInfo(
            id=self.keycloak_user_id,
            **user_settings.model_dump(context={'expose_secrets': True}),
        )

    async def get_authenticated_git_url(self, repository: str) -> str:
        # This would need to be implemented based on the git provider tokens
        # For now, return a basic HTTPS URL
        return f'https://github.com/{repository}.git'

    async def get_latest_token(self, provider_type: ProviderType) -> str | None:
        # Return the appropriate token from git_provider_tokens
        if self.git_provider_tokens:
            return self.git_provider_tokens.get(provider_type)
        return None

    async def get_secrets(self) -> dict[str, str]:
        """Get secrets for the user, including custom secrets."""
        # Get secrets from the secrets store
        secrets = await self.secrets_store.load()
        
        # Add custom secrets (e.g., from Slack integration)
        if self.custom_secrets:
            secrets.update(self.custom_secrets)
        
        return secrets