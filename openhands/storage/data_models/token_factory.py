

from abc import ABC, abstractmethod
from typing import Literal

from pydantic import BaseModel, SecretStr

from openhands.integrations.github.github_service import GithubServiceImpl


class TokenFactory(BaseModel, ABC):

    @abstractmethod
    async def get_token(self) -> str:
        """Get the current secret value"""


class ApiKey(TokenFactory):
    """ Secret Factory for Static API Keys. get_token simply returns the same secret value each time"""
    secret_value: SecretStr
    type: Literal["ApiKey"] = "ApiKey"

    async def get_token(self) -> str:
        return self.secret_value.get_token_value()


class GithubToken(TokenFactory):
    """ Secret Factory for github tokens. """
    github_user_id: str | None
    token: SecretStr | None
    type: Literal["GithubToken"] = "GithubToken"

    async def get_token(self) -> str:
        service = GithubServiceImpl(user_id=self.github_user_id)
        service.token = self.token
        token = await service.get_latest_token()
        return token
