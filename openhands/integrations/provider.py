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


PROVIDER_TOKEN_TYPE = dict[ProviderType, ProviderToken]
CUSTOM_SECRETS_TYPE = dict[str, SecretStr]


class SecretStore(BaseModel):
    provider_tokens: PROVIDER_TOKEN_TYPE = {}

    @field_serializer('provider_tokens')
    def provider_tokens_serializer(
        self, provider_tokens: PROVIDER_TOKEN_TYPE, info: SerializationInfo
    ):
        context = info.context
        if context and context.get('expose_secrets', False):
            tokens = {}
            for token_type, provider_token in provider_tokens.items():
                token_dict = (
                    provider_token.__dict__.copy()
                )  # Copy all attributes of token_obj
                if provider_token.token:
                    token_dict['token'] = (
                        provider_token.token.get_secret_value()
                    )  # Expose secret if it exists
                tokens[token_type] = token_dict
            return tokens

        return pydantic_encoder(provider_tokens)


class ProviderHandler:
    def __init__(self, secret_store: SecretStore):
        self.service_class_map = {
            ProviderType.GITHUB: GithubServiceImpl,
            ProviderType.GITLAB: GitLabServiceImpl,
        }

        self.provider_tokens = secret_store.provider_tokens

    def get_user(self):
        pass
