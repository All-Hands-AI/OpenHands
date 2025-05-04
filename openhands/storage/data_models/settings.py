from __future__ import annotations

from pydantic import BaseModel

from openhands.core.config.llm_config import LLMConfig
from openhands.core.config.utils import load_app_config


class Settings(BaseModel):
    """
    Persisted settings for OpenHands sessions.
    Secrets are handled separately by the SecretsStore.
    """

    language: str | None = None
    agent: str | None = None
    max_iterations: int | None = None
    security_analyzer: str | None = None
    confirmation_mode: bool | None = None
    llm_model: str | None = None
    llm_base_url: str | None = None
    remote_runtime_resource_factor: int | None = None
    enable_default_condenser: bool = True
    enable_sound_notifications: bool = False
    user_consents_to_analytics: bool | None = None
    sandbox_base_container_image: str | None = None
    sandbox_runtime_container_image: str | None = None

    model_config = {
        'validate_assignment': True,
    }

    @staticmethod
    def from_config() -> Settings | None:
        app_config = load_app_config()
        llm_config: LLMConfig = app_config.get_llm_config()
        security = app_config.security
        settings = Settings(
            language='en',
            agent=app_config.default_agent,
            max_iterations=app_config.max_iterations,
            security_analyzer=security.security_analyzer,
            confirmation_mode=security.confirmation_mode,
            llm_model=llm_config.model,
            llm_base_url=llm_config.base_url,
            remote_runtime_resource_factor=app_config.sandbox.remote_runtime_resource_factor,
        )
        return settings
