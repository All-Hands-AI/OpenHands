from __future__ import annotations

from types import MappingProxyType
from typing import Annotated, Any, Coroutine, Literal, overload

from pydantic import (
    BaseModel,
    Field,
    SecretStr,
    WithJsonSchema,
)

from openhands.core.logger import openhands_logger as logger
from openhands.events.action.action import Action
from openhands.events.action.commands import CmdRunAction
from openhands.events.stream import EventStream
from openhands.integrations.bitbucket.bitbucket_service import BitbucketService
from openhands.integrations.github.github_service import GithubServiceImpl
from openhands.integrations.gitlab.gitlab_service import GitLabServiceImpl
from openhands.integrations.service_types import (
    AuthenticationError,
    Branch,
    GitService,
    ProviderType,
    Repository,
    SuggestedTask,
    User,
)
from openhands.server.types import AppMode


class ProviderToken(BaseModel):
    token: SecretStr | None = Field(default=None)
    user_id: str | None = Field(default=None)
    host: str | None = Field(default=None)

    model_config = {
        'frozen': True,  # Makes the entire model immutable
        'validate_assignment': True,
    }

    @classmethod
    def from_value(cls, token_value: ProviderToken | dict[str, str]) -> ProviderToken:
        """Factory method to create a ProviderToken from various input types"""
        if isinstance(token_value, cls):
            return token_value
        elif isinstance(token_value, dict):
            token_str = token_value.get('token', '')
            # Override with emtpy string if it was set to None
            # Cannot pass None to SecretStr
            if token_str is None:
                token_str = ''
            user_id = token_value.get('user_id')
            host = token_value.get('host')
            return cls(token=SecretStr(token_str), user_id=user_id, host=host)

        else:
            raise ValueError('Unsupported Provider token type')


class CustomSecret(BaseModel):
    secret: SecretStr = Field(default_factory=lambda: SecretStr(''))
    description: str = Field(default='')

    model_config = {
        'frozen': True,  # Makes the entire model immutable
        'validate_assignment': True,
    }

    @classmethod
    def from_value(cls, secret_value: CustomSecret | dict[str, str]) -> CustomSecret:
        """Factory method to create a ProviderToken from various input types"""
        if isinstance(secret_value, CustomSecret):
            return secret_value
        elif isinstance(secret_value, dict):
            secret = secret_value.get('secret')
            description = secret_value.get('description')
            return cls(secret=SecretStr(secret), description=description)

        else:
            raise ValueError('Unsupport Provider token type')


PROVIDER_TOKEN_TYPE = MappingProxyType[ProviderType, ProviderToken]
CUSTOM_SECRETS_TYPE = MappingProxyType[str, CustomSecret]
PROVIDER_TOKEN_TYPE_WITH_JSON_SCHEMA = Annotated[
    PROVIDER_TOKEN_TYPE,
    WithJsonSchema({'type': 'object', 'additionalProperties': {'type': 'string'}}),
]
CUSTOM_SECRETS_TYPE_WITH_JSON_SCHEMA = Annotated[
    CUSTOM_SECRETS_TYPE,
    WithJsonSchema({'type': 'object', 'additionalProperties': {'type': 'string'}}),
]


class ProviderHandler:
    def __init__(
        self,
        provider_tokens: PROVIDER_TOKEN_TYPE,
        external_auth_id: str | None = None,
        external_auth_token: SecretStr | None = None,
        external_token_manager: bool = False,
    ):
        if not isinstance(provider_tokens, MappingProxyType):
            raise TypeError(
                f'provider_tokens must be a MappingProxyType, got {type(provider_tokens).__name__}'
            )

        self.service_class_map: dict[ProviderType, type[GitService]] = {
            ProviderType.GITHUB: GithubServiceImpl,
            ProviderType.GITLAB: GitLabServiceImpl,
            ProviderType.BITBUCKET: BitbucketService,
        }

        self.external_auth_id = external_auth_id
        self.external_auth_token = external_auth_token
        self.external_token_manager = external_token_manager
        self._provider_tokens = provider_tokens

    @property
    def provider_tokens(self) -> PROVIDER_TOKEN_TYPE:
        """Read-only access to provider tokens."""
        return self._provider_tokens

    def _get_service(self, provider: ProviderType) -> GitService:
        """Helper method to instantiate a service for a given provider"""
        token = self.provider_tokens[provider]
        service_class = self.service_class_map[provider]
        return service_class(
            user_id=token.user_id,
            external_auth_id=self.external_auth_id,
            external_auth_token=self.external_auth_token,
            token=token.token,
            external_token_manager=self.external_token_manager,
            base_domain=token.host,
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

    async def _get_latest_provider_token(
        self, provider: ProviderType
    ) -> SecretStr | None:
        """Get latest token from service"""
        service = self._get_service(provider)
        return await service.get_latest_token()

    async def get_repositories(self, sort: str, app_mode: AppMode) -> list[Repository]:
        """
        Get repositories from providers
        """

        all_repos: list[Repository] = []
        for provider in self.provider_tokens:
            try:
                service = self._get_service(provider)
                service_repos = await service.get_repositories(sort, app_mode)
                all_repos.extend(service_repos)
            except Exception as e:
                logger.warning(f'Error fetching repos from {provider}: {e}')

        return all_repos

    async def get_suggested_tasks(self) -> list[SuggestedTask]:
        """
        Get suggested tasks from providers
        """
        tasks: list[SuggestedTask] = []
        for provider in self.provider_tokens:
            try:
                service = self._get_service(provider)
                service_repos = await service.get_suggested_tasks()
                tasks.extend(service_repos)
            except Exception as e:
                logger.warning(f'Error fetching repos from {provider}: {e}')

        return tasks

    async def search_repositories(
        self,
        query: str,
        per_page: int,
        sort: str,
        order: str,
    ) -> list[Repository]:
        all_repos: list[Repository] = []
        for provider in self.provider_tokens:
            try:
                service = self._get_service(provider)
                service_repos = await service.search_repositories(
                    query, per_page, sort, order
                )
                all_repos.extend(service_repos)
            except Exception as e:
                logger.warning(f'Error searching repos from {provider}: {e}')
                continue

        return all_repos

    async def set_event_stream_secrets(
        self,
        event_stream: EventStream,
        env_vars: dict[ProviderType, SecretStr] | None = None,
    ) -> None:
        """
        This ensures that the latest provider tokens are masked from the event stream
        It is called when the provider tokens are first initialized in the runtime or when tokens are re-exported with the latest working ones

        Args:
            event_stream: Agent session's event stream
            env_vars: Dict of providers and their tokens that require updating
        """
        if env_vars:
            exposed_env_vars = self.expose_env_vars(env_vars)
        else:
            exposed_env_vars = await self.get_env_vars(expose_secrets=True)
        event_stream.set_secrets(exposed_env_vars)

    def expose_env_vars(
        self, env_secrets: dict[ProviderType, SecretStr]
    ) -> dict[str, str]:
        """
        Return string values instead of typed values for environment secrets
        Called just before exporting secrets to runtime, or setting secrets in the event stream
        """
        exposed_envs = {}
        for provider, token in env_secrets.items():
            env_key = ProviderHandler.get_provider_env_key(provider)
            exposed_envs[env_key] = token.get_secret_value()

        return exposed_envs

    @overload
    def get_env_vars(
        self,
        expose_secrets: Literal[True],
        providers: list[ProviderType] | None = ...,
        get_latest: bool = False,
    ) -> Coroutine[Any, Any, dict[str, str]]: ...

    @overload
    def get_env_vars(
        self,
        expose_secrets: Literal[False],
        providers: list[ProviderType] | None = ...,
        get_latest: bool = False,
    ) -> Coroutine[Any, Any, dict[ProviderType, SecretStr]]: ...

    async def get_env_vars(
        self,
        expose_secrets: bool = False,
        providers: list[ProviderType] | None = None,
        get_latest: bool = False,
    ) -> dict[ProviderType, SecretStr] | dict[str, str]:
        """
        Retrieves the provider tokens from ProviderHandler object
        This is used when initializing/exporting new provider tokens in the runtime

        Args:
            expose_secrets: Flag which returns strings instead of secrets
            providers: Return provider tokens for the list passed in, otherwise return all available providers
            get_latest: Get the latest working token for the providers if True, otherwise get the existing ones
        """

        if not self.provider_tokens:
            return {}

        env_vars: dict[ProviderType, SecretStr] = {}
        all_providers = [provider for provider in ProviderType]
        provider_list = providers if providers else all_providers

        for provider in provider_list:
            if provider in self.provider_tokens:
                token = (
                    self.provider_tokens[provider].token
                    if self.provider_tokens
                    else SecretStr('')
                )

                if get_latest:
                    token = await self._get_latest_provider_token(provider)

                if token:
                    env_vars[provider] = token

        if not expose_secrets:
            return env_vars

        return self.expose_env_vars(env_vars)

    @classmethod
    def check_cmd_action_for_provider_token_ref(
        cls, event: Action
    ) -> list[ProviderType]:
        """
        Detect if agent run action is using a provider token (e.g $GITHUB_TOKEN)
        Returns a list of providers which are called by the agent
        """

        if not isinstance(event, CmdRunAction):
            return []

        called_providers = []
        for provider in ProviderType:
            if ProviderHandler.get_provider_env_key(provider) in event.command.lower():
                called_providers.append(provider)

        return called_providers

    @classmethod
    def get_provider_env_key(cls, provider: ProviderType) -> str:
        """
        Map ProviderType value to the environment variable name in the runtime
        """
        return f'{provider.value}_token'.lower()

    async def verify_repo_provider(
        self, repository: str, specified_provider: ProviderType | None = None
    ) -> Repository:
        if specified_provider:
            try:
                service = self._get_service(specified_provider)
                return await service.get_repository_details_from_repo_name(repository)
            except Exception:
                pass

        for provider in self.provider_tokens:
            try:
                service = self._get_service(provider)
                return await service.get_repository_details_from_repo_name(repository)
            except Exception:
                pass

        raise AuthenticationError(f'Unable to access repo {repository}')

    async def get_branches(
        self, repository: str, specified_provider: ProviderType | None = None
    ) -> list[Branch]:
        """
        Get branches for a repository

        Args:
            repository: The repository name
            specified_provider: Optional provider type to use

        Returns:
            A list of branches for the repository
        """
        all_branches: list[Branch] = []

        if specified_provider:
            try:
                service = self._get_service(specified_provider)
                branches = await service.get_branches(repository)
                return branches
            except Exception as e:
                logger.warning(
                    f'Error fetching branches from {specified_provider}: {e}'
                )

        for provider in self.provider_tokens:
            try:
                service = self._get_service(provider)
                branches = await service.get_branches(repository)
                all_branches.extend(branches)
                # If we found branches, no need to check other providers
                if all_branches:
                    break
            except Exception as e:
                logger.warning(f'Error fetching branches from {provider}: {e}')

        # Sort branches by last push date (newest first)
        all_branches.sort(
            key=lambda b: b.last_push_date if b.last_push_date else '', reverse=True
        )

        # Move main/master branch to the top if it exists
        main_branches = []
        other_branches = []

        for branch in all_branches:
            if branch.name.lower() in ['main', 'master']:
                main_branches.append(branch)
            else:
                other_branches.append(branch)

        return main_branches + other_branches
