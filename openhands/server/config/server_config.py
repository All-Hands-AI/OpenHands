import os
from typing import Any

from pydantic import BaseModel, Field

from openhands.core.logger import openhands_logger as logger
from openhands.server.types import AppMode, ServerConfigInterface
from openhands.utils.import_utils import get_impl


class FeatureFlags(BaseModel):
    """Feature flags configuration."""

    enable_billing: bool = Field(default=False)
    hide_llm_settings: bool = Field(default=False)


class ServerConfig(ServerConfigInterface, BaseModel):
    """Server configuration."""

    # Pydantic model fields for configuration
    app_mode: AppMode = Field(default=AppMode.OSS)
    github_client_id: str = Field(default=os.environ.get('GITHUB_APP_CLIENT_ID', ''))
    posthog_client_key: str = Field(
        default='phc_3ESMmY9SgqEAGBB6sMGK5ayYHkeUuknH2vP6FmWH9RA'
    )
    attach_session_middleware_path: str = Field(default='')
    config_path: str | None = Field(default=None)
    config_cls: str | None = Field(default=os.environ.get('OPENHANDS_CONFIG_CLS', None))

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
    feature_flags: FeatureFlags = Field(default=FeatureFlags())

    def verify_config(self) -> None:
        """Verify configuration settings."""
        if self.config_cls:
            raise ValueError('Unexpected config path provided')


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
