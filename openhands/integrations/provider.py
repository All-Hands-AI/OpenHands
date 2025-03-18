from __future__ import annotations

from enum import Enum
from types import MappingProxyType
from typing import Any, Coroutine, Literal, overload

from pydantic import (
    BaseModel,
    Field,
    SecretStr,
    SerializationInfo,
    field_serializer,
    model_validator,
)
from pydantic.json import pydantic_encoder

from openhands.events.action.action import Action
from openhands.events.action.commands import CmdRunAction
from openhands.events.stream import EventStream
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
    token: SecretStr | None = Field(default=None)
    user_id: str | None = Field(default=None)

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


PROVIDER_TOKEN_TYPE = MappingProxyType[ProviderType, ProviderToken]
CUSTOM_SECRETS_TYPE = MappingProxyType[str, SecretStr]


class SecretStore(BaseModel):
    provider_tokens: PROVIDER_TOKEN_TYPE = Field(
        default_factory=lambda: MappingProxyType({})
    )

    model_config = {
        'frozen': True,
        'validate_assignment': True,
        'arbitrary_types_allowed': True,
    }

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

    @model_validator(mode='before')
    @classmethod
    def convert_dict_to_mappingproxy(
        cls, data: dict[str, dict[str, dict[str, str]]] | PROVIDER_TOKEN_TYPE
    ) -> dict[str, MappingProxyType]:
        """Custom deserializer to convert dictionary into MappingProxyType"""
        if not isinstance(data, dict):
            raise ValueError('SecretStore must be initialized with a dictionary')

        new_data = {}

        if 'provider_tokens' in data:
            tokens = data['provider_tokens']
            if isinstance(
                tokens, dict
            ):  # Ensure conversion happens only for dict inputs
                converted_tokens = {}
                for key, value in tokens.items():
                    try:
                        provider_type = (
                            ProviderType(key) if isinstance(key, str) else key
                        )
                        converted_tokens[provider_type] = ProviderToken.from_value(
                            value
                        )
                    except ValueError:
                        # Skip invalid provider types or tokens
                        continue

                # Convert to MappingProxyType
                new_data['provider_tokens'] = MappingProxyType(converted_tokens)

        return new_data


class ProviderHandler:
    def __init__(
        self,
        provider_tokens: PROVIDER_TOKEN_TYPE,
        external_auth_id: str | None = None,
        external_auth_token: SecretStr | None = None,
        external_token_manager: bool = False,
    ):
        self.service_class_map: dict[ProviderType, type[GitService]] = {
            ProviderType.GITHUB: GithubServiceImpl,
            ProviderType.GITLAB: GitLabServiceImpl,
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

    @classmethod
    def set_event_stream_secrets(
        cls,
        event_stream: EventStream,
        provider_tokens: PROVIDER_TOKEN_TYPE
        | dict[ProviderType, SecretStr]
        | dict[str, str],
    ):
        """
        This function sets the secret values for the event stream.
        This ensures that the latest provider tokens are masked from the event stream.
        It is called when the provider tokens are first initialized in the runtime, or when the provider tokens are re-exported with the latest working ones


        Args:
            event_stream: Agent session's event stream
            provider_tokens: Dict of providers and their tokens that require setting/updating

        """

        normalized_dict = {
            ProviderHandler.get_provider_env_key(provider, lower=True)
            if isinstance(provider, ProviderType)
            else provider: token
            for provider, token in provider_tokens.items()
        }

        for provider, raw_token in normalized_dict.items():
            token: str

            if isinstance(raw_token, ProviderToken):
                token = raw_token.token.get_secret_value() if raw_token.token else ''
            elif isinstance(raw_token, SecretStr):
                token = raw_token.get_secret_value()
            elif isinstance(raw_token, str):
                token = raw_token
            else:
                continue  # Skip invalid token types

            if token:
                event_stream.set_secrets({provider: token})

    @overload
    def get_env_vars(
        self,
        expose_secrets: Literal[True],
        required_providers: list[ProviderType] | None = ...,
        get_latest: bool = False,
    ) -> Coroutine[Any, Any, dict[str, str]]: ...

    @overload
    def get_env_vars(
        self,
        expose_secrets: Literal[False],
        required_providers: list[ProviderType] | None = ...,
        get_latest: bool = False,
    ) -> Coroutine[Any, Any, dict[ProviderType, SecretStr]]: ...

    async def get_env_vars(
        self,
        expose_secrets: bool = False,
        required_providers: list[ProviderType] | None = None,
        get_latest: bool = False,
    ) -> dict[ProviderType, SecretStr] | dict[str, str]:
        """
        Retrieves the provider tokens from ProviderHandler object
        This is used when initializing/exporting new provider tokens in the runtime

        Args:
            expose_secrets: Flag which returns strings instead of secrets
            required_providers: Return provider tokens for the list passed in, otherwise return all available providers
            get_latest: Get the latest working token for the providers if True, otherwise get the existing ones
        """

        if not self.provider_tokens:
            return {}

        env_vars: dict[ProviderType, SecretStr] = {}
        all_providers = [provider for provider in ProviderType]
        provider_list = required_providers if required_providers else all_providers

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

        exposed_envs = {}
        for provider, token in env_vars.items():
            env_key = ProviderHandler.get_provider_env_key(provider, lower=True)
            exposed_envs[env_key] = token.get_secret_value()

        return exposed_envs

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
            if ProviderHandler.get_provider_env_key(provider) in event.command:
                called_providers.append(provider)

        return called_providers

    @classmethod
    def get_provider_env_key(cls, provider: ProviderType, lower: bool = False) -> str:
        """
        Map ProviderType value to the environment variable name in the runtime
        """
        env_key = f'${provider.value.upper()}_TOKEN'
        if lower:
            return env_key.lower()

        return env_key.upper()
