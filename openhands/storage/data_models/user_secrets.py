from types import MappingProxyType
from typing import Any

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    SecretStr,
    SerializationInfo,
    field_serializer,
    model_validator,
)
from pydantic.json import pydantic_encoder

from openhands.integrations.provider import (
    CUSTOM_SECRETS_TYPE,
    PROVIDER_TOKEN_TYPE,
    PROVIDER_TOKEN_TYPE_WITH_JSON_SCHEMA,
    ProviderToken,
)
from openhands.integrations.service_types import ProviderType


class UserSecrets(BaseModel):
    provider_tokens: PROVIDER_TOKEN_TYPE_WITH_JSON_SCHEMA = Field(
        default_factory=lambda: MappingProxyType({})
    )

    custom_secrets: CUSTOM_SECRETS_TYPE = Field(
        default_factory=lambda: MappingProxyType({})
    )

    model_config = ConfigDict(
        frozen=True,
        validate_assignment=True,
        arbitrary_types_allowed=True,
    )

    @field_serializer('provider_tokens')
    def provider_tokens_serializer(
        self, provider_tokens: PROVIDER_TOKEN_TYPE, info: SerializationInfo
    ) -> dict[str, dict[str, str | Any]]:
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

    @field_serializer('custom_secrets')
    def custom_secrets_serializer(
        self, custom_secrets: CUSTOM_SECRETS_TYPE, info: SerializationInfo
    ):
        secrets = {}
        expose_secrets = info.context and info.context.get('expose_secrets', False)

        if custom_secrets:
            for secret_name, secret_key in custom_secrets.items():
                secrets[secret_name] = (
                    secret_key.get_secret_value()
                    if expose_secrets
                    else pydantic_encoder(secret_key)
                )
        return secrets

    @model_validator(mode='before')
    @classmethod
    def convert_dict_to_mappingproxy(
        cls, data: dict[str, dict[str, Any] | MappingProxyType] | PROVIDER_TOKEN_TYPE
    ) -> dict[str, MappingProxyType | None]:
        """Custom deserializer to convert dictionary into MappingProxyType"""
        if not isinstance(data, dict):
            raise ValueError('UserSecrets must be initialized with a dictionary')

        new_data: dict[str, MappingProxyType | None] = {}

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
            elif isinstance(tokens, MappingProxyType):
                new_data['provider_tokens'] = tokens

        if 'custom_secrets' in data:
            secrets = data['custom_secrets']
            if isinstance(secrets, dict):
                converted_secrets = {}
                for key, value in secrets.items():
                    if isinstance(value, str):
                        converted_secrets[key] = SecretStr(value)
                    elif isinstance(value, SecretStr):
                        converted_secrets[key] = value

                new_data['custom_secrets'] = MappingProxyType(converted_secrets)
            elif isinstance(secrets, MappingProxyType):
                new_data['custom_secrets'] = secrets

        return new_data
