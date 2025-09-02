"""Context provider system for dependency injection."""

from __future__ import annotations

from typing import TYPE_CHECKING

from openhands.utils.import_utils import get_impl

if TYPE_CHECKING:
    from fastapi import Request

    from .server_context import ServerContext

# Global variable to store the configured context class
_context_class: str | None = None


def set_context_class(context_class: str) -> None:
    """Set the server context class to use globally.

    This allows SaaS implementations to configure their own context class
    without modifying OpenHands code. The context class will be used for
    all requests unless overridden at the request level.

    Args:
        context_class: Fully qualified name of the ServerContext implementation
                      e.g., 'myapp.context.SaaSServerContext'

    Example:
        # In SaaS application startup
        from openhands.server.context import set_context_class
        set_context_class('saas.context.EnterpriseServerContext')
    """
    global _context_class
    _context_class = context_class


def get_context_class() -> str:
    """Get the currently configured context class name.

    Returns:
        str: Fully qualified name of the context class, or default if none set
    """
    return (
        _context_class
        or 'openhands.server.context.default_server_context.DefaultServerContext'
    )


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

    # Import here to avoid circular imports
    from .server_context import ServerContext

    # Get the configured context class or use default
    context_cls_name = get_context_class()
    context_cls = get_impl(ServerContext, context_cls_name)

    # Create new context instance
    context = context_cls()

    # Cache on request for subsequent use
    request.state.server_context = context
    return context


def create_server_context(context_class: str | None = None) -> ServerContext:
    """Create a server context instance directly.

    This is useful for testing, CLI applications, or other scenarios where
    you need a context outside of a FastAPI request.

    Args:
        context_class: Optional context class name. If None, uses the globally
                      configured class or default.

    Returns:
        ServerContext: New context instance

    Example:
        # For testing
        context = create_server_context('tests.mocks.MockServerContext')

        # Use default/configured context
        context = create_server_context()
    """
    # Import here to avoid circular imports
    from .server_context import ServerContext

    context_cls_name = context_class or get_context_class()
    context_cls = get_impl(ServerContext, context_cls_name)
    return context_cls()
