from __future__ import annotations
from abc import ABC, abstractmethod
import os
from fastapi import Request
from pydantic import SecretStr

from openhands.integrations.provider import PROVIDER_TOKEN_TYPE
from openhands.utils.import_utils import get_impl


class UserAuth(ABC):
    """Extensible class encapsulating user Authentication"""

    @abstractmethod
    async def get_user_id(self) -> str | None:
        """Get the unique identifier for the current user"""

    @abstractmethod
    async def get_access_token(self) -> SecretStr:
        """Get the access token for the current user"""

    @abstractmethod
    async def get_provider_tokens(self) -> PROVIDER_TOKEN_TYPE:
        """Get the provider tokens for the current user."""

    @classmethod
    @abstractmethod
    async def get_instance(cls, request: Request) -> UserAuth:
        """Get an instance of UserAuth from the request given"""


async def get_user_auth(request: Request) -> UserAuth:
    impl_name = os.environ.get('USER_AUTH_CLASS') or UserAuth.__class__.__qualname__
    impl: UserAuth = get_impl(UserAuth, impl_name)
    result = await impl.get_instance(request)
    return result
