import os
from typing import Any, ClassVar

from pydantic import BaseModel, Field

from openhands.core.logger import openhands_logger as logger
from openhands.server.types import AppMode, ServerConfigInterface
from openhands.utils.import_utils import get_impl


class FeatureFlags(BaseModel):
    """Feature flags configuration."""

    ENABLE_BILLING: bool
    HIDE_LLM_SETTINGS: bool


class ServerConfig(ServerConfigInterface, BaseModel):
    """Server configuration."""

    # Class variables required by ServerConfigInterface
    APP_MODE: ClassVar[AppMode] = AppMode.OSS
    GITHUB_CLIENT_ID: ClassVar[str] = os.environ.get('GITHUB_APP_CLIENT_ID', '')
    POSTHOG_CLIENT_KEY: ClassVar[str] = (
        'phc_3ESMmY9SgqEAGBB6sMGK5ayYHkeUuknH2vP6FmWH9RA'
    )
    ATTACH_SESSION_MIDDLEWARE_PATH: ClassVar[str] = ''
    CONFIG_PATH: ClassVar[str | None] = None

    # Configuration attributes
    config_cls: ClassVar[str | None] = os.environ.get('OPENHANDS_CONFIG_CLS', None)

    # Pydantic model fields for configuration
    app_mode: AppMode = Field(default=APP_MODE)
    github_client_id: str = Field(default=GITHUB_CLIENT_ID)
    posthog_client_key: str = Field(default=POSTHOG_CLIENT_KEY)
    enable_billing: bool = Field(
        default=os.environ.get('ENABLE_BILLING', 'false') == 'true'
    )
    hide_llm_settings: bool = Field(
        default=os.environ.get('HIDE_LLM_SETTINGS', 'false') == 'true'
    )
    app_slug: str | None = Field(default=None)
    stripe_publishable_key: str | None = Field(default=None)

    # Server implementation classes
    settings_store_class: str = Field(
        default='openhands.storage.settings.file_settings_store.FileSettingsStore'
    )
    secret_store_class: str = Field(
        default='openhands.storage.secrets.file_secrets_store.FileSecretsStore'
    )
    conversation_store_class: str = Field(
        default='openhands.storage.conversation.file_conversation_store.FileConversationStore'
    )
    conversation_manager_class: str = Field(
        default='openhands.server.conversation_manager.standalone_conversation_manager.StandaloneConversationManager'
    )
    monitoring_listener_class: str = Field(
        default='openhands.server.monitoring.MonitoringListener'
    )
    user_auth_class: str = Field(
        default='openhands.server.user_auth.default_user_auth.DefaultUserAuth'
    )

    def verify_config(self) -> None:
        """Verify configuration settings."""
        if self.config_cls:
            raise ValueError('Unexpected config path provided')

    def get_config(self) -> dict[str, Any]:
        """Get server configuration.

        Returns:
            dict[str, Any]: Server configuration as a dictionary.
        """
        return {
            'APP_MODE': self.app_mode,
            'GITHUB_CLIENT_ID': self.github_client_id,
            'POSTHOG_CLIENT_KEY': self.posthog_client_key,
            'FEATURE_FLAGS': {
                'ENABLE_BILLING': self.enable_billing,
                'HIDE_LLM_SETTINGS': self.hide_llm_settings,
            },
            'APP_SLUG': self.app_slug,
            'STRIPE_PUBLISHABLE_KEY': self.stripe_publishable_key,
        }


def load_server_config() -> ServerConfigInterface:
    config_cls = os.environ.get('OPENHANDS_CONFIG_CLS', None)
    logger.info(f'Using config class {config_cls}')

    server_config_cls = get_impl(ServerConfig, config_cls)

    # Initialize the server config with default values
    enable_billing = os.environ.get('ENABLE_BILLING', 'false') == 'true'
    hide_llm_settings = os.environ.get('HIDE_LLM_SETTINGS', 'false') == 'true'

    server_config: ServerConfigInterface = server_config_cls(
        enable_billing=enable_billing, hide_llm_settings=hide_llm_settings
    )
    server_config.verify_config()

    return server_config
