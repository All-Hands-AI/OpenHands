from enum import Enum

from pydantic import BaseModel, SecretStr, SerializationInfo, field_serializer
from pydantic.json import pydantic_encoder

from openhands.integrations.github.github_service import GithubServiceImpl
from openhands.integrations.gitlab.gitlab_service import GitLabServiceImpl


class ProviderType(Enum):
    GITHUB = 'github'
    GITLAB = 'gitlab'


class ProviderToken(BaseModel):
    token: SecretStr | None
    user_id: str | None


PROVIDER_TOKEN_TYPE = dict[ProviderType, ProviderToken | str]
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
            if not provider_token:
                continue
                
            token_type_str = token_type.value if isinstance(token_type, ProviderType) else str(token_type)
            
            if isinstance(provider_token, ProviderToken) and provider_token.token:
                tokens[token_type_str] = provider_token.token.get_secret_value() if expose_secrets else '**********'
            elif isinstance(provider_token, (str, SecretStr)):
                # Convert to ProviderToken if needed
                token_obj = self._convert_token(provider_token)
                if token_obj.token:
                    tokens[token_type_str] = token_obj.token.get_secret_value() if expose_secrets else '**********'
        
        return tokens


class ProviderHandler:
    def __init__(self, secret_store: SecretStore):
        self.service_class_map = {
            ProviderType.GITHUB: GithubServiceImpl,
            ProviderType.GITLAB: GitLabServiceImpl,
        }

        self.provider_tokens = secret_store.provider_tokens

    def get_user(self):
        pass
