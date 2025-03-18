from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, SecretStr, model_validator, field_validator
from pydantic.json import pydantic_encoder

from openhands.integrations.github.github_service import GithubServiceImpl
from openhands.integrations.gitlab.gitlab_service import GitLabServiceImpl
from openhands.integrations.git_service import GitService


class ProviderType(Enum):
    GITHUB = "github"
    GITLAB = "gitlab"


class ProviderToken(BaseModel):
    """Immutable token for a provider service"""
    token: Optional[SecretStr] = Field(frozen=True)
    user_id: Optional[str] = Field(default=None, frozen=True)

    model_config = {
        'frozen': True,
        'validate_assignment': True,
    }

    @field_validator('token', mode='before')
    @classmethod
    def convert_token(cls, v):
        """Convert string tokens to SecretStr"""
        if isinstance(v, str):
            return SecretStr(v)
        return v


class ProviderTokens(BaseModel):
    """Immutable mapping of provider types to tokens"""
    tokens: dict[ProviderType, ProviderToken] = Field(default_factory=dict)

    model_config = {
        'frozen': True,
        'validate_assignment': True,
    }

    @model_validator(mode='before')
    @classmethod
    def convert_tokens(cls, values):
        """Convert raw token values to ProviderToken objects"""
        if not isinstance(values, dict):
            return values
            
        raw_tokens = values.get('tokens', {})
        converted = {}
        
        for key, value in raw_tokens.items():
            if isinstance(key, str):
                try:
                    key = ProviderType(key)
                except ValueError:
                    continue
                    
            if not value:
                continue
                
            if isinstance(value, ProviderToken):
                converted[key] = value
            elif isinstance(value, dict):
                converted[key] = ProviderToken(
                    token=value.get('token'),
                    user_id=value.get('user_id')
                )
            elif isinstance(value, (str, SecretStr)):
                converted[key] = ProviderToken(token=value)
                
        values['tokens'] = converted
        return values

    def get(self, provider: ProviderType) -> Optional[ProviderToken]:
        """Safely get a provider token"""
        return self.tokens.get(provider)


class SecretStore(BaseModel):
    """Store for provider tokens and other secrets"""
    provider_tokens: ProviderTokens = Field(default_factory=ProviderTokens)

    model_config = {
        'frozen': True,
        'validate_assignment': True,
    }

    @field_validator('provider_tokens', mode='before')
    @classmethod
    def ensure_provider_tokens(cls, v):
        """Ensure provider_tokens is a ProviderTokens instance"""
        if isinstance(v, dict):
            return ProviderTokens(tokens=v)
        return v


class ProviderHandler:
    """Handler for provider services"""
    def __init__(
        self,
        provider_tokens: dict[ProviderType, ProviderToken] | ProviderTokens,
        external_auth_token: Optional[SecretStr] = None,
    ):
        self.service_class_map: dict[ProviderType, type[GitService]] = {
            ProviderType.GITHUB: GithubServiceImpl,
            ProviderType.GITLAB: GitLabServiceImpl,
        }

        # Convert to ProviderTokens if needed
        if isinstance(provider_tokens, dict):
            provider_tokens = ProviderTokens(tokens=provider_tokens)

        self._secret_store = SecretStore(provider_tokens=provider_tokens)
        self._external_auth_token = external_auth_token

    @property
    def provider_tokens(self) -> dict[ProviderType, ProviderToken]:
        """Read-only access to provider tokens"""
        return self._secret_store.provider_tokens.tokens

    @property
    def external_auth_token(self) -> Optional[SecretStr]:
        """Read-only access to external auth token"""
        return self._external_auth_token

    def _get_service(self, provider: ProviderType) -> GitService:
        """Helper method to instantiate a service for a given provider"""
        service_class = self.service_class_map.get(provider)
        if not service_class:
            raise ValueError(f"Unsupported provider: {provider}")

        token = self._secret_store.provider_tokens.get(provider)
        if not token or not token.token:
            raise ValueError(f"No token available for provider: {provider}")

        return service_class(token.token, self._external_auth_token)