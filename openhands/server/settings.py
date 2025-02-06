from __future__ import annotations

from pydantic import BaseModel, SecretStr, SerializationInfo, field_serializer
from pydantic.json import pydantic_encoder

from openhands.core.config.llm_config import LLMConfig
from openhands.core.config.utils import load_app_config


class Settings(BaseModel):
    """
    Persisted settings for OpenHands sessions
    """

    language: str | None = None
    agent: str | None = None
    max_iterations: int | None = None
    security_analyzer: str | None = None
    confirmation_mode: bool | None = None
    llm_model: str | None = None
    llm_api_key: SecretStr | None = None
    llm_base_url: str | None = None
    remote_runtime_resource_factor: int | None = None
    github_token: SecretStr | None = None
    enable_default_condenser: bool = False
    user_consents_to_analytics: bool | None = None

    @field_serializer('llm_api_key')
    def llm_api_key_serializer(self, llm_api_key: SecretStr, info: SerializationInfo):
        """Custom serializer for the LLM API key.

        To serialize the API key instead of ********, set expose_secrets to True in the serialization context.
        """
        context = info.context
        if context and context.get('expose_secrets', False):
            return llm_api_key.get_secret_value()

        return pydantic_encoder(llm_api_key)

    @field_serializer('github_token')
    def github_token_serializer(
        self, github_token: SecretStr | None, info: SerializationInfo
    ):
        """Custom serializer for the GitHub token.

        To serialize the token instead of ********, set expose_secrets to True in the serialization context.
        """
        if github_token is None:
            return None

        context = info.context
        if context and context.get('expose_secrets', False):
            return github_token.get_secret_value()

        return pydantic_encoder(github_token)

    @staticmethod
    def from_config() -> Settings | None:
        app_config = load_app_config()
        llm_config: LLMConfig = app_config.get_llm_config()
        if llm_config.api_key is None:
            # If no api key has been set, we take this to mean that there is no reasonable default
            return None
        security = app_config.security
        settings = Settings(
            language='en',
            agent=app_config.default_agent,
            max_iterations=app_config.max_iterations,
            security_analyzer=security.security_analyzer,
            confirmation_mode=security.confirmation_mode,
            llm_model=llm_config.model,
            llm_api_key=llm_config.api_key,
            llm_base_url=llm_config.base_url,
            remote_runtime_resource_factor=app_config.sandbox.remote_runtime_resource_factor,
            github_token=None,
        )
        return settings


class POSTSettingsModel(Settings):
    """
    Settings for POST requests
    """

    unset_github_token: bool | None = None
    github_token: str | None = (
        None  # This is a string because it's coming from the frontend
    )

    # Override the serializer for the GitHub token to handle the string input
    @field_serializer('github_token')
    def github_token_serializer(self, github_token: str | None):
        return github_token


class GETSettingsModel(Settings):
    """
    Settings with additional token data for the frontend
    """

    github_token_is_set: bool | None = None
