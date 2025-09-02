"""Base ServerContext class for dependency injection and extensibility."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import socketio

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


class ServerContext(ABC):
    """Base class for server context that holds all server dependencies.

    This replaces the global variables in shared.py and allows for:
    - Dependency injection for better testability
    - Easy extensibility for SaaS and enterprise features
    - Per-request contexts for multi-user scenarios
    - No import-time dependencies on environment variables

    SaaS implementations can extend this class to provide:
    - Custom server configurations with enterprise features
    - Multi-tenant storage implementations
    - Per-user/per-organization contexts
    - Custom conversation managers and monitoring

    Example SaaS extension:
        class SaaSServerContext(ServerContext):
            def __init__(self, user_id: str, org_id: str):
                super().__init__()
                self.user_id = user_id
                self.org_id = org_id

            def get_server_config(self) -> ServerConfig:
                return SaaSServerConfig(org_id=self.org_id)

            def get_file_store(self) -> FileStore:
                return MultiTenantFileStore(self.user_id, self.org_id)
    """

    @abstractmethod
    def get_config(self) -> OpenHandsConfig:
        """Get the OpenHands configuration.

        Returns:
            OpenHandsConfig: The core application configuration
        """
        raise NotImplementedError

    @abstractmethod
    def get_server_config(self) -> ServerConfig:
        """Get the server configuration.

        Returns:
            ServerConfig: Server-specific configuration including feature flags,
                         authentication settings, and component class names
        """
        raise NotImplementedError

    @abstractmethod
    def get_file_store(self) -> FileStore:
        """Get the file store implementation.

        Returns:
            FileStore: File storage implementation for handling uploads,
                      downloads, and file management
        """
        raise NotImplementedError

    @abstractmethod
    def get_socketio_server(self) -> socketio.AsyncServer:
        """Get the Socket.IO server instance.

        Returns:
            socketio.AsyncServer: The Socket.IO server for real-time communication
        """
        raise NotImplementedError

    @abstractmethod
    def get_conversation_manager(self) -> ConversationManager:
        """Get the conversation manager implementation.

        Returns:
            ConversationManager: Manager for handling conversation lifecycle,
                               agent sessions, and conversation state
        """
        raise NotImplementedError

    @abstractmethod
    def get_monitoring_listener(self) -> MonitoringListener:
        """Get the monitoring listener implementation.

        Returns:
            MonitoringListener: Listener for monitoring events and metrics
        """
        raise NotImplementedError

    @abstractmethod
    def get_settings_store_class(self) -> type[SettingsStore]:
        """Get the settings store class.

        Returns:
            type[SettingsStore]: Class for storing and retrieving user settings
        """
        raise NotImplementedError

    @abstractmethod
    def get_secrets_store_class(self) -> type[SecretsStore]:
        """Get the secrets store class.

        Returns:
            type[SecretsStore]: Class for storing and retrieving user secrets
        """
        raise NotImplementedError

    @abstractmethod
    def get_conversation_store_class(self) -> type[ConversationStore]:
        """Get the conversation store class.

        Returns:
            type[ConversationStore]: Class for storing and retrieving conversations
        """
        raise NotImplementedError
