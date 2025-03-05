from enum import Enum
from typing import Any

from pydantic import BaseModel, SecretStr, SerializationInfo, field_serializer
from pydantic.json import pydantic_encoder

from openhands.integrations.github.github_service import GithubServiceImpl
from openhands.integrations.gitlab.gitlab_service import GitLabServiceImpl
from openhands.integrations.service_types import (
    AuthenticationError,
    GitService,
    Repository,
    SuggestedTask,
    User,
)


class ProviderType(Enum):
    GITHUB = 'github'
    GITLAB = 'gitlab'


class ProviderToken(BaseModel):
    token: SecretStr | None
    user_id: str | None


PROVIDER_TOKEN_TYPE = dict[ProviderType, ProviderToken]
CUSTOM_SECRETS_TYPE = dict[str, SecretStr]


class SecretStore(BaseModel):
    provider_tokens: PROVIDER_TOKEN_TYPE = {}

    @classmethod
    def _convert_token(cls, token_value: str | ProviderToken | SecretStr) -> ProviderToken:
        if isinstance(token_value, ProviderToken):
            return token_value
        elif isinstance(token_value, str):
            return ProviderToken(token=SecretStr(token_value), user_id=None)
        elif isinstance(token_value, SecretStr):
            return ProviderToken(token=token_value, user_id=None)
        else:
            raise ValueError(f"Invalid token type: {type(token_value)}")

    def model_post_init(self, __context) -> None:
        # Convert any string tokens to ProviderToken objects
        converted_tokens = {}
        for token_type, token_value in self.provider_tokens.items():
            if token_value:  # Only convert non-empty tokens
                try:
                    if isinstance(token_type, str):
                        token_type = ProviderType(token_type)
                    converted_tokens[token_type] = self._convert_token(token_value)
                except ValueError:
                    # Skip invalid provider types or tokens
                    continue
        self.provider_tokens = converted_tokens

    @field_serializer('provider_tokens')
    def provider_tokens_serializer(
        self, provider_tokens: PROVIDER_TOKEN_TYPE, info: SerializationInfo
    ):
        tokens = {}
        expose_secrets = info.context and info.context.get('expose_secrets', False)
        
        for token_type, provider_token in provider_tokens.items():
            if not provider_token or not provider_token.token:
                continue
                
            token_type_str = token_type.value if isinstance(token_type, ProviderType) else str(token_type)
            tokens[token_type_str] = {
                'token': provider_token.token.get_secret_value() if expose_secrets else '**********',
                'user_id': provider_token.user_id
            }
        
        return tokens


class ProviderHandler:
    def __init__(self, provider_tokens: PROVIDER_TOKEN_TYPE, idp_token: SecretStr | None = None):
        self.service_class_map: dict[ProviderType, GitService] = {
            ProviderType.GITHUB: GithubServiceImpl,
            ProviderType.GITLAB: GitLabServiceImpl,
        }

        self.provider_tokens = provider_tokens
        self.idp_token = idp_token

    async def _get_service(self, provider: ProviderType) -> GitService:
        """Helper method to instantiate a service for a given provider"""
        token = self.provider_tokens.get(provider)
        if not token:
            raise AuthenticationError(f"No token found for {provider.value}")
        
        service_class = self.service_class_map[provider]
        return service_class(
            user_id=token.user_id,
            idp_token=self.idp_token,
            token=token.token
        )

    async def get_user(self) -> User:
        """Get user information from the first available provider"""
        for provider in self.provider_tokens:
            try:
                service = await self._get_service(provider)
                return await service.get_user()
            except Exception:
                continue
        raise AuthenticationError("Need valid provider token")

    async def get_latest_token(self) -> SecretStr:
        """Get latest token from GitHub service"""
        service = await self._get_service(ProviderType.GITHUB)
        return await service.get_latest_token()

    async def get_latest_provider_token(self) -> SecretStr:
        """Get latest provider token from GitHub service"""
        service = await self._get_service(ProviderType.GITHUB)
        return await service.get_latest_provider_token()

    async def get_repositories(
        self, page: int, per_page: int, sort: str, installation_id: int | None
    ) -> list[Repository]:
        """Get repositories from all available providers"""
        all_repos = []
        for provider in self.provider_tokens:
            try:
                service = await self._get_service(provider)
                repos = await service.get_repositories(page, per_page, sort, installation_id)
                all_repos.extend(repos)
            except Exception:
                continue
        return all_repos

    async def get_installation_ids(self) -> list[int]:
        """Get installation IDs from GitHub service"""
        service = await self._get_service(ProviderType.GITHUB)
        return await service.get_installation_ids()

    async def search_repositories(
        self, query: str, per_page: int, sort: str, order: str
    ) -> list[Repository]:
        """Search repositories across all available providers"""
        all_repos = []
        for provider in self.provider_tokens:
            try:
                service = await self._get_service(provider)
                repos = await service.search_repositories(query, per_page, sort, order)
                all_repos.extend(repos)
            except Exception:
                continue
        return all_repos

    async def execute_graphql_query(
        self, query: str, variables: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute GraphQL query on GitHub service"""
        service = await self._get_service(ProviderType.GITHUB)
        return await service.execute_graphql_query(query, variables)

    async def get_suggested_tasks(self) -> list[SuggestedTask]:
        """Get suggested tasks from all available providers"""
        all_tasks = []
        for provider in self.provider_tokens:
            try:
                service = await self._get_service(provider)
                tasks = await service.get_suggested_tasks()
                all_tasks.extend(tasks)
            except Exception:
                continue
        return all_tasks