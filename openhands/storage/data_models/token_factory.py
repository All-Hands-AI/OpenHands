from abc import ABC, abstractmethod
from typing import Literal

from pydantic import BaseModel, SecretStr, SerializationInfo, field_serializer
from pydantic.json import pydantic_encoder

from openhands.integrations.github.github_service import GithubServiceImpl


class TokenFactory(BaseModel, ABC):
    @abstractmethod
    async def get_token(self) -> str:
        """Get the current secret value"""


class ApiKey(TokenFactory):
    """Secret Factory for Static API Keys. get_token simply returns the same secret value each time"""

    secret_value: SecretStr
    type: Literal['ApiKey'] = 'ApiKey'

    async def get_token(self) -> str:
        return self.secret_value.get_secret_value()

    @field_serializer('secret_value')
    def llm_api_key_serializer(self, secret_value: SecretStr, info: SerializationInfo):
        """Custom serializer for the secret_value.

        To serialize the API key instead of ********, set expose_secrets to True in the serialization context.
        """
        context = info.context
        if context and context.get('expose_secrets', False):
            return secret_value.get_secret_value()

        return pydantic_encoder(secret_value)


class GithubToken(TokenFactory):
    """Secret Factory for github tokens."""

    github_user_id: str | None
    token: SecretStr | None
    type: Literal['GithubToken'] = 'GithubToken'

    async def get_token(self) -> str:
        service = GithubServiceImpl(user_id=self.github_user_id)
        service.token = self.token
        token = await service.get_latest_token()
        return token

    @field_serializer('token')
    def llm_api_key_serializer(self, token: SecretStr | None, info: SerializationInfo):
        """Custom serializer for the token.

        To serialize the API key instead of ********, set expose_secrets to True in the serialization context.
        """
        context = info.context
        if self.token is not None and context and context.get('expose_secrets', False):
            return self.token.get_secret_value()

        return pydantic_encoder(token)
