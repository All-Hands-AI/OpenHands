from dataclasses import dataclass
from typing import Callable

from fastapi import Depends

from openhands.app_server.user.user_models import UserInfo
from openhands.app_server.user.user_service import UserService, UserServiceManager
from openhands.sdk.conversation.secret_source import SecretSource, StaticSecret

from openhands.integrations.provider import ProviderHandler, ProviderType
from openhands.server.user_auth.user_auth import UserAuth, get_user_auth


# In legacy mode for OSS, there is only a single unconstrained user
ROOT_USER = 'root'


@dataclass
class LegacyUserService(UserService):
    """Interface to old user settings service. Eventually we want to migrate
    this to use true database asyncio. """

    user_auth: UserAuth
    _user_info: UserInfo | None = None
    _provider_handler: ProviderHandler | None = None

    async def get_user_id(self) -> str:
        # If you have an auth object here you are logged in. If user_id is None
        # it means we are in OSS mode.
        user_id = (await self.user_auth.get_user_id()) or ROOT_USER
        return user_id

    async def get_user_info(self) -> UserInfo:
        user_info = self._user_info
        if user_info is None:
            user_id = await self.get_user_id()
            settings = await self.user_auth.get_user_settings()
            assert settings is not None
            user_info = UserInfo(
                id=user_id,
                **settings.model_dump(context={'expose_secrets': True}),
            )
            self._user_info = user_info
        return user_info

    async def get_provider_handler(self):
        provider_handler = self._provider_handler
        if not provider_handler:
            provider_tokens = await self.user_auth.get_provider_tokens()
            assert provider_tokens is not None
            user_id = await self.get_user_id()
            provider_handler = ProviderHandler(provider_tokens=provider_tokens, external_auth_id=user_id)
            self._provider_handler = provider_handler
        return provider_handler

    async def get_authenticated_git_url(self, repository: str) -> str:
        provider_handler = await self.get_provider_handler()
        url = await provider_handler.get_authenticated_git_url(repository)
        return url

    async def get_latest_token(self, provider_type: ProviderType) -> str | None:
        provider_handler = await self.get_provider_handler()
        service = provider_handler.get_service(provider_type)
        token = await service.get_latest_token()
        return token

    async def get_secrets(self) -> dict[str, SecretSource]:
        results = {}

        # Include custom secrets...
        secrets = await self.user_auth.get_user_secrets()
        if secrets:
            for name, value in secrets.custom_secrets.items():
                results[name] = StaticSecret(value)

        return results

class LegacyUserServiceManager(UserServiceManager):
    def get_resolver_for_current_user(self) -> Callable:
        return resolve_for_user


def resolve_for_user(
    user_auth: UserAuth = Depends(get_user_auth),
) -> UserService:
    return LegacyUserService(user_auth=user_auth)
