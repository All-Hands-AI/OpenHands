"""Example SaaS extension demonstrating the new context system.

This example shows how a SaaS implementation can extend OpenHands
with enterprise features using the new ServerContext system.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from openhands.server.context import ServerContext

# Conditional imports to avoid dependency issues in testing
try:
    from openhands.server.config.server_config import ServerConfig
    from openhands.server.types import AppMode
except ImportError:
    # Create mock classes for testing
    class ServerConfig:
        def __init__(self):
            self.app_mode = 'SAAS'
            self.enable_billing = True
            self.conversation_manager_class = 'default'
            self.settings_store_class = 'default'
            self.secret_store_class = 'default'
            self.conversation_store_class = 'default'

        def get_config(self):
            return {}

    class AppMode:
        SAAS = 'SAAS'


if TYPE_CHECKING:
    from openhands.storage.files import FileStore


class SaaSServerConfig(ServerConfig):
    """SaaS-specific server configuration with enterprise features."""

    def __init__(self, org_id: str | None = None):
        super().__init__()
        self.org_id = org_id
        # Override app mode for SaaS
        self.app_mode = AppMode.SAAS
        # Enable enterprise features
        self.enable_billing = True
        # Use enterprise-specific implementations
        self.conversation_manager_class = (
            'examples.saas_conversation_manager.MultiTenantConversationManager'
        )
        self.settings_store_class = 'examples.saas_stores.MultiTenantSettingsStore'
        self.secret_store_class = 'examples.saas_stores.MultiTenantSecretsStore'
        self.conversation_store_class = (
            'examples.saas_stores.MultiTenantConversationStore'
        )

    def get_config(self):
        """Override to include enterprise-specific configuration."""
        config = super().get_config()
        config.update(
            {
                'ORG_ID': self.org_id,
                'FEATURE_FLAGS': {
                    **config.get('FEATURE_FLAGS', {}),
                    'ENABLE_BILLING': True,
                    'MULTI_TENANT': True,
                    'ENTERPRISE_FEATURES': True,
                },
            }
        )
        return config


class MultiTenantFileStore:
    """Example multi-tenant file store that isolates files by organization."""

    def __init__(self, user_id: str, org_id: str, base_store: FileStore):
        self.user_id = user_id
        self.org_id = org_id
        self.base_store = base_store

    def get_path_prefix(self) -> str:
        """Get the path prefix for this tenant."""
        return f'orgs/{self.org_id}/users/{self.user_id}'

    # Implement FileStore interface with tenant isolation
    # (This is just an example - real implementation would be more complex)


class SaaSServerContext(ServerContext):
    """SaaS server context with multi-tenant support.

    This context provides:
    - Per-organization configuration
    - Multi-tenant storage isolation
    - Enterprise-specific features
    - User-scoped contexts
    """

    def __init__(self, user_id: str, org_id: str):
        super().__init__()
        self.user_id = user_id
        self.org_id = org_id

        # Initialize with tenant-specific values
        self._config = None
        self._server_config = None
        self._file_store = None
        self._socketio_server = None
        self._conversation_manager = None
        self._monitoring_listener = None
        self._settings_store_class = None
        self._secrets_store_class = None
        self._conversation_store_class = None

    def get_config(self):
        """Get configuration with tenant-specific overrides."""
        if self._config is None:
            from openhands.core.config import load_openhands_config

            # Load base config and apply tenant-specific overrides
            self._config = load_openhands_config()
            # Apply tenant-specific configuration here
            # e.g., different file store paths, API keys, etc.
        return self._config

    def get_server_config(self):
        """Get SaaS-specific server configuration."""
        if self._server_config is None:
            self._server_config = SaaSServerConfig(org_id=self.org_id)
        return self._server_config

    def get_file_store(self):
        """Get multi-tenant file store."""
        if self._file_store is None:
            from openhands.storage import get_file_store

            config = self.get_config()

            # Create base file store
            base_store = get_file_store(
                file_store_type=config.file_store,
                file_store_path=config.file_store_path,
                file_store_web_hook_url=config.file_store_web_hook_url,
                file_store_web_hook_headers=config.file_store_web_hook_headers,
                file_store_web_hook_batch=config.file_store_web_hook_batch,
            )

            # Wrap with multi-tenant isolation
            self._file_store = MultiTenantFileStore(
                self.user_id, self.org_id, base_store
            )
        return self._file_store

    def get_socketio_server(self):
        """Get Socket.IO server with tenant-aware namespacing."""
        if self._socketio_server is None:
            import socketio

            # Create Socket.IO server with tenant-aware configuration
            # In a real implementation, you might use namespaces for tenant isolation
            self._socketio_server = socketio.AsyncServer(
                async_mode='asgi',
                cors_allowed_origins='*',
                # Add tenant-specific configuration
                max_http_buffer_size=4 * 1024 * 1024,
            )
        return self._socketio_server

    def get_conversation_manager(self):
        """Get multi-tenant conversation manager."""
        if self._conversation_manager is None:
            # This would load a custom multi-tenant conversation manager
            # that isolates conversations by organization
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

            # Pass tenant information to the conversation manager
            self._conversation_manager = ConversationManagerImpl.get_instance(
                sio,
                config,
                file_store,
                server_config,
                monitoring_listener,
                user_id=self.user_id,
                org_id=self.org_id,  # Additional tenant params
            )
        return self._conversation_manager

    def get_monitoring_listener(self):
        """Get monitoring listener with tenant-aware metrics."""
        if self._monitoring_listener is None:
            from openhands.server.monitoring import MonitoringListener
            from openhands.utils.import_utils import get_impl

            server_config = self.get_server_config()
            config = self.get_config()

            MonitoringListenerImpl = get_impl(
                MonitoringListener,
                server_config.monitoring_listener_class,
            )

            # Create monitoring listener with tenant context
            self._monitoring_listener = MonitoringListenerImpl.get_instance(
                config, user_id=self.user_id, org_id=self.org_id
            )
        return self._monitoring_listener

    def get_settings_store_class(self):
        """Get multi-tenant settings store class."""
        if self._settings_store_class is None:
            from openhands.storage.settings.settings_store import SettingsStore
            from openhands.utils.import_utils import get_impl

            server_config = self.get_server_config()
            self._settings_store_class = get_impl(
                SettingsStore, server_config.settings_store_class
            )
        return self._settings_store_class

    def get_secrets_store_class(self):
        """Get multi-tenant secrets store class."""
        if self._secrets_store_class is None:
            from openhands.storage.secrets.secrets_store import SecretsStore
            from openhands.utils.import_utils import get_impl

            server_config = self.get_server_config()
            self._secrets_store_class = get_impl(
                SecretsStore, server_config.secret_store_class
            )
        return self._secrets_store_class

    def get_conversation_store_class(self):
        """Get multi-tenant conversation store class."""
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


# Example usage in SaaS application
def setup_saas_context():
    """Example of how SaaS would set up the context system."""
    from openhands.server.context import set_context_class

    # Configure the context class globally
    set_context_class('examples.saas_extension.SaaSServerContext')

    print('✓ SaaS context configured')


# Example FastAPI route using the context
async def example_saas_route(request, context: ServerContext):
    """Example route showing how SaaS can use the context system."""
    # Get tenant-specific configuration
    context.get_config()
    server_config = context.get_server_config()

    # Access tenant information if available
    if hasattr(context, 'user_id') and hasattr(context, 'org_id'):
        user_id = context.user_id
        org_id = context.org_id

        return {
            'message': 'SaaS route with tenant context',
            'user_id': user_id,
            'org_id': org_id,
            'app_mode': server_config.app_mode.value,
            'enterprise_features': server_config.get_config().get('FEATURE_FLAGS', {}),
        }
    else:
        return {
            'message': 'SaaS route with default context',
            'app_mode': server_config.app_mode.value,
        }


if __name__ == '__main__':
    # Example of how this would be used
    setup_saas_context()

    # Create a tenant-specific context
    saas_context = SaaSServerContext(user_id='user123', org_id='org456')

    # Use the context
    server_config = saas_context.get_server_config()
    print(f'App mode: {server_config.app_mode}')
    print(f'Organization: {saas_context.org_id}')
    print(f'User: {saas_context.user_id}')
    print('✓ SaaS extension example completed')
