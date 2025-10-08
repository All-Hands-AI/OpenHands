from dataclasses import dataclass
from typing import Any, AsyncGenerator

from fastapi import Request
from pydantic import PrivateAttr

from openhands.app_server.services.injector import InjectorState
from openhands.app_server.user.admin_user_context import USER_CONTEXT_ATTR
from openhands.app_server.user.user_context import UserContext, UserContextInjector
from openhands.app_server.user.user_models import UserInfo
from openhands.integrations.provider import ProviderHandler, ProviderType
from openhands.sdk.conversation.secret_source import SecretSource, StaticSecret
from openhands.server.user_auth.user_auth import UserAuth, get_user_auth
from openhands.utils.import_utils import get_impl


@dataclass
class AuthUserContext(UserContext):
    """Interface to old user settings service. Eventually we want to migrate
    this to use true database asyncio."""

    user_auth: UserAuth
    _user_info: UserInfo | None = None
    _provider_handler: ProviderHandler | None = None

    async def get_user_id(self) -> str | None:
        # If you have an auth object here you are logged in. If user_id is None
        # it means we are in OSS mode.
        user_id = await self.user_auth.get_user_id()
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
            provider_handler = ProviderHandler(
                provider_tokens=provider_tokens, external_auth_id=user_id
            )
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
            for name, custom_secret in secrets.custom_secrets.items():
                results[name] = StaticSecret(value=custom_secret.secret)

        return results


USER_ID_ATTR = 'user_id'


class AuthUserContextInjector(UserContextInjector):
    _user_auth_class: Any = PrivateAttr(default=None)

    async def inject(self, state: InjectorState) -> AsyncGenerator[UserContext, None]:
        user_context = getattr(state, USER_CONTEXT_ATTR, None)
        if user_context is None:
            # Get the user_id from the request state
            user_id = getattr(state, USER_ID_ATTR)
            assert user_id is not None

            # Get the user auth class from the config
            user_auth_class = self._user_auth_class
            if user_auth_class is None:
                from openhands.server.config.server_config import load_server_config

                impl_name = load_server_config().user_auth_class
                user_auth_class = get_impl(UserAuth, impl_name)
                self._user_auth_class = user_auth_class

            user_auth = await user_auth_class.get_for_user(user_id)
            user_context = AuthUserContext(user_auth=user_auth)
            setattr(state, USER_CONTEXT_ATTR, user_context)

        yield user_context

    async def depends(self, request: Request) -> AsyncGenerator[UserContext, None]:  # type: ignore
        user_context = getattr(request.state, USER_CONTEXT_ATTR, None)
        if user_context is None:
            user_auth = await get_user_auth(request)
            user_context = AuthUserContext(user_auth=user_auth)
            setattr(request.state, 'user_context', user_context)
        yield user_context
