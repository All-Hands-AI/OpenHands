import os
from importlib.metadata import EntryPoint, entry_points

from openhands.core.logger import openhands_logger as logger
from openhands.server.types import AppMode, ServerConfigInterface
from openhands.utils.import_utils import get_impl


class ServerConfig(ServerConfigInterface):
    config_cls = os.environ.get('OPENHANDS_CONFIG_CLS', None)
    app_mode = AppMode.OSS
    posthog_client_key = 'phc_3ESMmY9SgqEAGBB6sMGK5ayYHkeUuknH2vP6FmWH9RA'
    github_client_id = os.environ.get('GITHUB_APP_CLIENT_ID', '')
    enable_billing = os.environ.get('ENABLE_BILLING', 'false') == 'true'
    hide_llm_settings = os.environ.get('HIDE_LLM_SETTINGS', 'false') == 'true'
    # This config is used to hide the microagent management page from the users for now. We will remove this once we release the new microagent management page.
    settings_store_class: str = (
        'openhands.storage.settings.file_settings_store.FileSettingsStore'
    )
    secret_store_class: str = (
        'openhands.storage.secrets.file_secrets_store.FileSecretsStore'
    )
    conversation_store_class: str = (
        'openhands.storage.conversation.file_conversation_store.FileConversationStore'
    )
    conversation_manager_class: str = os.environ.get(
        'CONVERSATION_MANAGER_CLASS',
        'openhands.server.conversation_manager.standalone_conversation_manager.StandaloneConversationManager',
    )
    monitoring_listener_class: str = 'openhands.server.monitoring.MonitoringListener'
    user_auth_class: str = (
        'openhands.server.user_auth.default_user_auth.DefaultUserAuth'
    )

    def verify_config(self):
        if self.config_cls:
            raise ValueError('Unexpected config path provided')

    def get_config(self):
        config = {
            'APP_MODE': self.app_mode,
            'GITHUB_CLIENT_ID': self.github_client_id,
            'POSTHOG_CLIENT_KEY': self.posthog_client_key,
            'FEATURE_FLAGS': {
                'ENABLE_BILLING': self.enable_billing,
                'HIDE_LLM_SETTINGS': self.hide_llm_settings,
            },
        }

        return config


def _load_server_config_from_entry_point() -> type[ServerConfig] | None:
    try:
        eps: list[EntryPoint] = list(
            entry_points().select(group='openhands_server_config')
        )
    except Exception:
        return None
    if not eps:
        return None
    if len(eps) > 1:
        logger.warning(
            'Multiple entry points found for openhands_server_config; using the first one: %s',
            eps[0].name,
        )
    ep = eps[0]
    loaded = ep.load()
    # Accept either a class or a callable returning a class
    if callable(loaded) and not isinstance(loaded, type):
        loaded = loaded()
    if isinstance(loaded, type) and issubclass(loaded, ServerConfig):
        return loaded
    # Fallback: allow any subclass of ServerConfigInterface via get_impl semantics
    try:
        if isinstance(loaded, type) and issubclass(loaded, ServerConfigInterface):
            return loaded  # type: ignore[return-value]
    except Exception:
        pass
    logger.error(
        'Entry point %s did not provide a ServerConfig class; ignoring', ep.name
    )
    return None


def load_server_config() -> ServerConfig:
    # Priority 1: explicit class via env var for backward compatibility
    config_cls = os.environ.get('OPENHANDS_CONFIG_CLS', None)
    if config_cls:
        logger.info(f'Using config class {config_cls} (env OPENHANDS_CONFIG_CLS)')
        server_config_cls = get_impl(ServerConfig, config_cls)
    else:
        # Priority 2: entry point discovery to allow external repos to supply config
        server_config_cls = _load_server_config_from_entry_point() or ServerConfig
        logger.info('Using config class %s (entry points/default)', server_config_cls)

    server_config: ServerConfig = server_config_cls()  # type: ignore[call-arg]
    server_config.verify_config()
    return server_config
