from dataclasses import dataclass
from typing import Callable

from fastapi import Request

from openhands.app_server.user.user_context import UserContext, UserContextInjector
from openhands.app_server.user.user_models import UserInfo
from openhands.integrations.provider import ProviderType
from openhands.sdk.conversation.secret_source import SecretSource


@dataclass
class AdminUserContext(UserContext):
    """User context for use in admin operations which allows access beyond the scope of a single user"""

    user_id: str | None

    async def get_user_id(self) -> str | None:
        return self.user_id

    async def get_user_info(self) -> UserInfo:
        raise NotImplementedError()

    async def get_authenticated_git_url(self, repository: str) -> str:
        raise NotImplementedError()

    async def get_latest_token(self, provider_type: ProviderType) -> str | None:
        raise NotImplementedError()

    async def get_secrets(self) -> dict[str, SecretSource]:
        raise NotImplementedError()


class AdminUserContextInjector(UserContextInjector):
    def get_injector(self) -> Callable:
        return resolve_admin

    async def get_for_user(self, user_id: str | None) -> UserContext:
        return AdminUserContext(user_id)


def resolve_admin(request: Request) -> UserContext:
    user_context = getattr(request.state, 'user_context')
    if user_context is None:
        user_context = AdminUserContext(user_id=None)
        setattr(request.state, 'user_context', user_context)
    return user_context
