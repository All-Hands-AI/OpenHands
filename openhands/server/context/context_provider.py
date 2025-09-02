"""Context provider system for dependency injection.

This module provides the default context provider for OpenHands routes.
For custom context implementations, use the factory pattern from
openhands.server.factory instead of modifying global state.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi import Request

from .server_context import ServerContext


async def get_server_context(request: Request) -> ServerContext:
    """Get server context from request, with caching.

    This function provides dependency injection for ServerContext. It:
    1. Checks if a context is already cached on the request
    2. If not, creates a new context using the configured context class
    3. Caches the context on the request for subsequent use

    This enables:
    - Per-request context instances for multi-user scenarios
    - Lazy initialization of dependencies
    - Easy testing with mock contexts

    Args:
        request: FastAPI request object

    Returns:
        ServerContext: The server context instance for this request

    Usage:
        from fastapi import Depends, Request
        from openhands.server.context import get_server_context, ServerContext

        @app.get('/example')
        async def example_route(
            request: Request,
            context: ServerContext = Depends(get_server_context)
        ):
            config = context.get_config()
            # ... use context
    """
    # Check if context is already cached on the request
    context = getattr(request.state, 'server_context', None)
    if context:
        return context

    # Create default context instance
    from .default_server_context import DefaultServerContext
    context = DefaultServerContext()

    # Cache on request for subsequent use
    request.state.server_context = context
    return context


def create_server_context(context_class: str | None = None) -> ServerContext:
    """Create a server context instance directly.

    This is useful for testing, CLI applications, or other scenarios where
    you need a context outside of a FastAPI request.

    Args:
        context_class: Optional context class name. If None, uses DefaultServerContext.

    Returns:
        ServerContext: New context instance

    Example:
        # For testing with custom context
        from openhands.utils.import_utils import get_impl
        context_cls = get_impl(ServerContext, 'tests.mocks.MockServerContext')
        context = context_cls()

        # Use default context
        context = create_server_context()
    """
    if context_class:
        from openhands.utils.import_utils import get_impl
        context_cls = get_impl(ServerContext, context_class)
        return context_cls()
    else:
        from .default_server_context import DefaultServerContext
        return DefaultServerContext()
