"""Server context system for dependency injection and extensibility.

This module provides a context-based approach to managing server dependencies,
replacing the global variables in shared.py. This enables:

- Dependency injection for better testability
- Easy extensibility for custom implementations
- Per-request contexts for multi-user scenarios
- No import-time dependencies on environment variables

Usage:
    # In route handlers
    from openhands.server.context import get_server_context

    @app.get('/example')
    async def example_route(
        request: Request,
        context: ServerContext = Depends(get_server_context)
    ):
        config = context.get_config()
        # ... use context instead of importing from shared

    # For custom extensions
    from openhands.server.context import set_context_class
    set_context_class('myapp.context.MyServerContext')
"""

from .context_provider import (
    create_server_context,
    get_context_class,
    get_server_context,
    set_context_class,
)
from .server_context import ServerContext

__all__ = [
    'ServerContext',
    'get_server_context',
    'set_context_class',
    'get_context_class',
    'create_server_context',
]
