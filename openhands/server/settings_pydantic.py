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


class POSTSettingsModel(BaseModel):
    """Model for handling POST requests to update settings"""
    unset_github_token: bool | None = None
    provider_tokens: dict[str, str | dict[str, str]] = Field(default_factory=dict)
    language: str | None = None
    agent: str | None = None
    max_iterations: int | None = None
    security_analyzer: str | None = None
    confirmation_mode: bool | None = None
    llm_model: str | None = None
    llm_api_key: SecretStr | None = None
    llm_base_url: str | None = None
    remote_runtime_resource_factor: int | None = None
    enable_default_condenser: bool | None = None
    enable_sound_notifications: bool | None = None
    user_consents_to_analytics: bool | None = None

    def to_settings(self, current_settings: Settings) -> Settings:
        """Convert POST model to Settings, preserving immutability"""
        # Start with a copy of current settings
        settings_dict = current_settings.model_dump()

        # Update non-token fields if they are provided
        for field, value in self.model_dump(
            exclude={'provider_tokens', 'unset_github_token'}
        ).items():
            if value is not None:
                settings_dict[field] = value

        # Handle provider tokens
        current_tokens = dict(current_settings.secrets_store.provider_tokens.tokens)
        
        for token_type_str, token_value in self.provider_tokens.items():
            try:
                token_type = ProviderType(token_type_str)
                if isinstance(token_value, dict):
                    token_str = token_value.get('token')
                    user_id = token_value.get('user_id')
                    if token_str:
                        current_tokens[token_type] = ProviderToken(
                            token=SecretStr(token_str),
                            user_id=user_id
                        )
                elif isinstance(token_value, str) and token_value:
                    current_tokens[token_type] = ProviderToken(
                        token=SecretStr(token_value)
                    )
            except ValueError:
                continue

        # Handle explicit token removal
        if self.unset_github_token:
            current_tokens.pop(ProviderType.GITHUB, None)

        settings_dict['secrets_store'] = SecretStore(
            provider_tokens=ProviderTokens(tokens=current_tokens)
        )
        
        return Settings(**settings_dict)


class GETSettingsModel(Settings):
    """Model for GET requests that hides sensitive information"""
    model_config = {
        'json_encoders': {
            SecretStr: lambda v: '***' if v else None,
        }
    }