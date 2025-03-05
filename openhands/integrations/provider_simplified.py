from enum import Enum
from pydantic import BaseModel, SecretStr, SerializationInfo, field_serializer

class ProviderType(Enum):
    GITHUB = 'github'
    GITLAB = 'gitlab'

class ProviderToken(BaseModel):
    token: SecretStr | None
    user_id: str | None = None

    @field_serializer('token')
    def serialize_token(self, token: SecretStr | None, info: SerializationInfo):
        if not token:
            return None
        expose_secrets = info.context and info.context.get('expose_secrets', False)
        return token.get_secret_value() if expose_secrets else '**********'

PROVIDER_TOKEN_TYPE = dict[ProviderType, ProviderToken]

class SecretStore(BaseModel):
    provider_tokens: PROVIDER_TOKEN_TYPE = {}

    @field_serializer('provider_tokens')
    def serialize_provider_tokens(self, tokens: PROVIDER_TOKEN_TYPE, info: SerializationInfo):
        return {
            provider.value: {
                'token': token.token,
                'user_id': token.user_id
            } if token and token.token else None
            for provider, token in tokens.items()
        }