from enum import Enum
from types import MappingProxyType
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, SecretStr, WithJsonSchema


class ProviderType(Enum):
    GITHUB = 'github'
    GITLAB = 'gitlab'
    BITBUCKET = 'bitbucket'
    ENTERPRISE_SSO = 'enterprise_sso'


class ProviderToken(BaseModel):
    token: SecretStr | None = Field(default=None)
    user_id: str | None = Field(default=None)
    host: str | None = Field(default=None)

    model_config = ConfigDict(
        frozen=True,  # Makes the entire model immutable
        validate_assignment=True,
    )

    @classmethod
    def from_value(
        cls, token_value: 'ProviderToken | dict[str, str]'
    ) -> 'ProviderToken':
        """Factory method to create a ProviderToken from various input types"""
        if isinstance(token_value, ProviderToken):
            return token_value
        elif isinstance(token_value, dict):
            token = token_value.get('token', '')
            user_id = token_value.get('user_id', '')
            host = token_value.get('host', '')
            return cls(
                token=SecretStr(token) if token else None,
                user_id=user_id if user_id else None,
                host=host if host else None,
            )
        else:
            raise ValueError('Unsupported Provider token type')


class CustomSecret(BaseModel):
    secret: SecretStr = Field(default_factory=lambda: SecretStr(''))
    description: str = Field(default='')

    model_config = ConfigDict(
        frozen=True,  # Makes the entire model immutable
        validate_assignment=True,
    )

    @classmethod
    def from_value(
        cls, secret_value: 'CustomSecret | dict[str, str]'
    ) -> 'CustomSecret':
        """Factory method to create a CustomSecret from various input types"""
        if isinstance(secret_value, CustomSecret):
            return secret_value
        elif isinstance(secret_value, dict):
            secret = secret_value.get('secret', '')
            description = secret_value.get('description', '')
            return cls(secret=SecretStr(secret), description=description)
        else:
            raise ValueError('Unsupported Provider token type')


# Type aliases
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
