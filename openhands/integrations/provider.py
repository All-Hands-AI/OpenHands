from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field, SecretStr, SerializationInfo, field_serializer
from pydantic.json import pydantic_encoder

from openhands.integrations.github.github_service import GithubServiceImpl
from openhands.integrations.gitlab.gitlab_service import GitLabServiceImpl
from openhands.integrations.service_types import (
    AuthenticationError,
    GitService,
    Repository,
    User,
)


class ProviderType(Enum):
    GITHUB = 'github'
    GITLAB = 'gitlab'


class ProviderToken(BaseModel):
    token: SecretStr | None = Field(default=None, frozen=True)
    user_id: str | None = Field(default=None, frozen=True)

    model_config = {
        'frozen': True,  # Makes the entire model immutable
        'validate_assignment': True,
    }

    @classmethod
    def from_value(cls, token_value: ProviderToken | dict[str, str]) -> ProviderToken:
        """Factory method to create a ProviderToken from various input types"""
        if isinstance(token_value, ProviderToken):
            return token_value
        elif isinstance(token_value, dict):
            token_str = token_value.get('token')
            user_id = token_value.get('user_id')
            return cls(token=SecretStr(token_str), user_id=user_id)

        else:
            raise ValueError('Unsupport Provider token type')


PROVIDER_TOKEN_TYPE = dict[ProviderType, ProviderToken]
CUSTOM_SECRETS_TYPE = dict[str, SecretStr]


class SecretStore(BaseModel):
    provider_tokens: PROVIDER_TOKEN_TYPE = Field(default_factory=dict, frozen=True)

    model_config = {
        'frozen': True,
        'validate_assignment': True,
    }

    @classmethod
    def create(
        cls, tokens: PROVIDER_TOKEN_TYPE | dict[str, dict[str, str]] | None = None
    ) -> SecretStore:
        """Factory method to create a new SecretStore with converted tokens"""
        if not tokens:
            return cls()

        converted_tokens = {}
        for token_type, token_value in tokens.items():
            if token_value:  # Only convert non-empty tokens
                try:
                    if isinstance(token_type, str):
                        token_type = ProviderType(token_type)
                    converted_tokens[token_type] = ProviderToken.from_value(token_value)
                except ValueError:
                    # Skip invalid provider types or tokens
                    continue

        # Convert to immutable mapping
        return cls(provider_tokens=converted_tokens)

    @field_serializer('provider_tokens')
    def provider_tokens_serializer(
        self, provider_tokens: PROVIDER_TOKEN_TYPE, info: SerializationInfo
    ):
        tokens = {}
        expose_secrets = info.context and info.context.get('expose_secrets', False)

        for token_type, provider_token in provider_tokens.items():
            if not provider_token or not provider_token.token:
                continue

            token_type_str = (
                token_type.value
                if isinstance(token_type, ProviderType)
                else str(token_type)
            )
            tokens[token_type_str] = {
                'token': provider_token.token.get_secret_value()
                if expose_secrets
                else pydantic_encoder(provider_token.token),
                'user_id': provider_token.user_id,
            }

        return tokens


class ProviderHandler:
    def __init__(
        self,
        provider_tokens: PROVIDER_TOKEN_TYPE,
        external_auth_token: SecretStr | None = None,
    ):
        self.service_class_map: dict[ProviderType, type[GitService]] = {
            ProviderType.GITHUB: GithubServiceImpl,
            ProviderType.GITLAB: GitLabServiceImpl,
        }

        # Create immutable copy through SecretStore
        self._secret_store = SecretStore.create(dict(provider_tokens))
        self.external_auth_token = external_auth_token

    @property
    def provider_tokens(self) -> PROVIDER_TOKEN_TYPE:
        """Read-only access to provider tokens"""
        return self._secret_store.provider_tokens

    def _get_service(self, provider: ProviderType) -> GitService:
        """Helper method to instantiate a service for a given provider"""
        token = self.provider_tokens[provider]
        service_class = self.service_class_map[provider]
        return service_class(
            user_id=token.user_id,
            external_auth_token=self.external_auth_token,
            token=token.token,
        )

    async def get_user(self) -> User:
        """Get user information from the first available provider"""
        for provider in self.provider_tokens:
            try:
                service = self._get_service(provider)
                return await service.get_user()
            except Exception:
                continue
        raise AuthenticationError('Need valid provider token')

    async def get_latest_provider_tokens(self) -> dict[ProviderType, SecretStr]:
        """Get latest token from services"""
        tokens = {}
        for provider in self.provider_tokens:
            service = self._get_service(provider)
            tokens[provider] = await service.get_latest_token()

        return tokens

    async def get_repositories(
        self, page: int, per_page: int, sort: str, installation_id: int | None
    ) -> list[Repository]:
        """Get repositories from all available providers"""
        all_repos = []
        for provider in self.provider_tokens:
            try:
                service = self._get_service(provider)
                repos = await service.get_repositories(
                    page, per_page, sort, installation_id
                )
                all_repos.extend(repos)
            except Exception:
                continue
        return all_repos
