"""Shared server dependencies - DEPRECATED.

This module is deprecated and maintained only for backward compatibility.
New code should use the context system from openhands.server.context instead.

The context system provides:
- Better dependency injection
- Easier testing and mocking
- SaaS extensibility
- Per-request contexts
- No import-time side effects

Migration guide:
    # Old way (deprecated)
    from openhands.server.shared import config, server_config

    # New way (recommended)
    from openhands.server.context import get_server_context

    @app.get('/example')
    async def example_route(
        request: Request,
        context: ServerContext = Depends(get_server_context)
    ):
        config = context.get_config()
        server_config = context.get_server_config()
"""

import warnings

from openhands.server.context.default_server_context import DefaultServerContext

# Load environment variables for backward compatibility
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    # dotenv is optional
    pass

# Create default context for backward compatibility
_default_context = DefaultServerContext()

# Issue deprecation warning when this module is imported
warnings.warn(
    'openhands.server.shared is deprecated. Use openhands.server.context instead. '
    'See the module docstring for migration guidance.',
    DeprecationWarning,
    stacklevel=2,
)


# Module-level lazy loading using __getattr__
def __getattr__(name: str):
    """Lazy loading for backward compatibility globals."""
    if name == 'config':
        return _default_context.get_config()
    elif name == 'server_config':
        return _default_context.get_server_config()
    elif name == 'file_store':
        return _default_context.get_file_store()
    elif name == 'sio':
        return _default_context.get_socketio_server()
    elif name == 'conversation_manager':
        return _default_context.get_conversation_manager()
    elif name == 'monitoring_listener':
        return _default_context.get_monitoring_listener()
    elif name == 'SettingsStoreImpl':
        return _default_context.get_settings_store_class()
    elif name == 'SecretsStoreImpl':
        return _default_context.get_secrets_store_class()
    elif name == 'ConversationStoreImpl':
        return _default_context.get_conversation_store_class()
    else:
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
