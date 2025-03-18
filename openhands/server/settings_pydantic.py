from __future__ import annotations

from pydantic import BaseModel, Field, SecretStr, model_validator

from openhands.integrations.provider_pydantic import (
    ProviderToken,
    ProviderTokens,
    ProviderType,
    SecretStore,
)


class Settings(BaseModel):
    """Application settings"""
    language: str | None = None
    agent: str | None = None
    max_iterations: int | None = None
    security_analyzer: str | None = None
    confirmation_mode: bool | None = None
    llm_model: str | None = None
    llm_api_key: SecretStr | None = None
    llm_base_url: str | None = None
    remote_runtime_resource_factor: int | None = None
    secrets_store: SecretStore = Field(default_factory=SecretStore)
    enable_default_condenser: bool = False
    enable_sound_notifications: bool = False
    user_consents_to_analytics: bool | None = None

    model_config = {
        'validate_assignment': True,
    }

    def with_updated_provider_token(
        self,
        provider_type: ProviderType,
        token: str | None,
        user_id: str | None = None
    ) -> Settings:
        """Creates a new Settings instance with updated provider token"""
        current_tokens = dict(self.secrets_store.provider_tokens.tokens)

        if token is None:
            current_tokens.pop(provider_type, None)
        else:
            current_tokens[provider_type] = ProviderToken(
                token=SecretStr(token),
                user_id=user_id
            )

        return self.model_copy(
            update={
                'secrets_store': SecretStore(
                    provider_tokens=ProviderTokens(tokens=current_tokens)
                )
            }
        )

    def with_removed_provider_token(self, provider_type: ProviderType) -> Settings:
        """Creates a new Settings instance with the specified provider token removed"""
        return self.with_updated_provider_token(provider_type, None)


class POSTSettingsModel(Settings):
    """Settings for POST requests"""
    unset_github_token: bool | None = None
    # Override provider_tokens to accept string tokens from frontend
    provider_tokens: dict[str, str] = Field(default_factory=dict)

    @field_serializer('provider_tokens')
    def provider_tokens_serializer(self, provider_tokens: dict[str, str]):
        return provider_tokens


class GETSettingsModel(Settings):
    """Model for GET requests that hides sensitive information"""
    model_config = {
        'json_encoders': {
            SecretStr: lambda v: '***' if v else None,
        }
    }