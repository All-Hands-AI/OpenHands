"""Default ServerContext implementation that maintains current behavior."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from openhands.server.context.server_context import ServerContext

# Lazy imports to avoid import-time dependencies

if TYPE_CHECKING:
    from openhands.core.config.openhands_config import OpenHandsConfig
    from openhands.server.config.server_config import ServerConfig
    from openhands.server.conversation_manager.conversation_manager import (
        ConversationManager,
    )
    from openhands.server.monitoring import MonitoringListener
    from openhands.storage.conversation.conversation_store import ConversationStore
    from openhands.storage.files import FileStore
    from openhands.storage.secrets.secrets_store import SecretsStore
    from openhands.storage.settings.settings_store import SettingsStore


class DefaultServerContext(ServerContext):
    """Default implementation that maintains current behavior.

    This implementation replicates the exact behavior of the original shared.py
    globals, ensuring backward compatibility while providing the extensibility
    framework for SaaS implementations.

    All dependencies are lazily initialized to avoid import-time side effects
    and allow for proper testing and mocking.
    """

    def __init__(self):
        # Lazy initialization - only create instances when requested
        self._config: OpenHandsConfig | None = None
        self._server_config: ServerConfig | None = None
        self._file_store: FileStore | None = None
        self._socketio_server = None
        self._conversation_manager: ConversationManager | None = None
        self._monitoring_listener: MonitoringListener | None = None
        self._settings_store_class: type[SettingsStore] | None = None
        self._secrets_store_class: type[SecretsStore] | None = None
        self._conversation_store_class: type[ConversationStore] | None = None

    def get_config(self) -> OpenHandsConfig:
        """Get the OpenHands configuration."""
        if self._config is None:
            from openhands.core.config import load_openhands_config

            self._config = load_openhands_config()
        return self._config

    def get_server_config(self) -> ServerConfig:
        """Get the server configuration."""
        if self._server_config is None:
            from openhands.server.config.server_config import load_server_config

            self._server_config = load_server_config()
        return self._server_config

    def get_file_store(self) -> FileStore:
        """Get the file store implementation."""
        if self._file_store is None:
            from openhands.storage import get_file_store

            config = self.get_config()
            self._file_store = get_file_store(
                file_store_type=config.file_store,
                file_store_path=config.file_store_path,
                file_store_web_hook_url=config.file_store_web_hook_url,
                file_store_web_hook_headers=config.file_store_web_hook_headers,
                file_store_web_hook_batch=config.file_store_web_hook_batch,
            )
        return self._file_store

    def get_socketio_server(self):
        """Get the Socket.IO server instance."""
        if self._socketio_server is None:
            import socketio

            # Replicate the original Redis client manager logic
            client_manager = None
            redis_host = os.environ.get('REDIS_HOST')
            if redis_host:
                client_manager = socketio.AsyncRedisManager(
                    f'redis://{redis_host}',
                    redis_options={'password': os.environ.get('REDIS_PASSWORD')},
                )

            self._socketio_server = socketio.AsyncServer(
                async_mode='asgi',
                cors_allowed_origins='*',
                client_manager=client_manager,
                # Increase buffer size to 4MB (to handle 3MB files with base64 overhead)
                max_http_buffer_size=4 * 1024 * 1024,
            )
        return self._socketio_server

    def get_conversation_manager(self) -> ConversationManager:
        """Get the conversation manager implementation."""
        if self._conversation_manager is None:
            from openhands.server.conversation_manager.conversation_manager import (
                ConversationManager,
            )
            from openhands.utils.import_utils import get_impl

            server_config = self.get_server_config()
            config = self.get_config()
            file_store = self.get_file_store()
            sio = self.get_socketio_server()
            monitoring_listener = self.get_monitoring_listener()

            ConversationManagerImpl = get_impl(
                ConversationManager,
                server_config.conversation_manager_class,
            )

            self._conversation_manager = ConversationManagerImpl.get_instance(
                sio, config, file_store, server_config, monitoring_listener
            )
        return self._conversation_manager

    def get_monitoring_listener(self) -> MonitoringListener:
        """Get the monitoring listener implementation."""
        if self._monitoring_listener is None:
            from openhands.server.monitoring import MonitoringListener
            from openhands.utils.import_utils import get_impl

            server_config = self.get_server_config()
            config = self.get_config()

            MonitoringListenerImpl = get_impl(
                MonitoringListener,
                server_config.monitoring_listener_class,
            )

            self._monitoring_listener = MonitoringListenerImpl.get_instance(config)
        return self._monitoring_listener

    def get_settings_store_class(self) -> type[SettingsStore]:
        """Get the settings store class."""
        if self._settings_store_class is None:
            from openhands.storage.settings.settings_store import SettingsStore
            from openhands.utils.import_utils import get_impl

            server_config = self.get_server_config()
            self._settings_store_class = get_impl(
                SettingsStore, server_config.settings_store_class
            )
        return self._settings_store_class

    def get_secrets_store_class(self) -> type[SecretsStore]:
        """Get the secrets store class."""
        if self._secrets_store_class is None:
            from openhands.storage.secrets.secrets_store import SecretsStore
            from openhands.utils.import_utils import get_impl

            server_config = self.get_server_config()
            self._secrets_store_class = get_impl(
                SecretsStore, server_config.secret_store_class
            )
        return self._secrets_store_class

    def get_conversation_store_class(self) -> type[ConversationStore]:
        """Get the conversation store class."""
        if self._conversation_store_class is None:
            from openhands.storage.conversation.conversation_store import (
                ConversationStore,
            )
            from openhands.utils.import_utils import get_impl

            server_config = self.get_server_config()
            self._conversation_store_class = get_impl(
                ConversationStore,
                server_config.conversation_store_class,
            )
        return self._conversation_store_class
