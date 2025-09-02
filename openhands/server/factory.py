"""FastAPI app factory for OpenHands server.

This module provides a factory function to create OpenHands FastAPI applications
with configurable dependencies, enabling external repositories to extend OpenHands
without relying on global variables or environment variable configuration.

Example usage for external repositories:

    # In your external repo
    from openhands.server.factory import create_openhands_app
    from my_custom_context import MyServerContext
    
    # Create OpenHands app with your custom context
    openhands_app = create_openhands_app(
        context_factory=lambda: MyServerContext(),
        include_oss_routes=False,  # Skip OSS-specific routes
        custom_lifespan=my_custom_lifespan
    )
    
    # Add your own routes
    @openhands_app.get('/my-custom-route')
    async def my_route():
        return {'message': 'Hello from my extension!'}
    
    # Or create your own app and include OpenHands routes
    from fastapi import FastAPI
    my_app = FastAPI()
    my_app.mount('/openhands', openhands_app)
"""

import contextlib
import warnings
from contextlib import asynccontextmanager
from typing import AsyncIterator, Callable, Optional

from fastapi import FastAPI
from fastapi.routing import Mount

with warnings.catch_warnings():
    warnings.simplefilter('ignore')

from fastapi import Request
from fastapi.responses import JSONResponse

import openhands.agenthub  # noqa F401 (we import this to get the agents registered)
from openhands import __version__
from openhands.integrations.service_types import AuthenticationError
from openhands.server.context.server_context import ServerContext
from openhands.server.routes.conversation import app as conversation_api_router
from openhands.server.routes.feedback import app as feedback_api_router
from openhands.server.routes.files import app as files_api_router
from openhands.server.routes.git import app as git_api_router
from openhands.server.routes.health import add_health_endpoints
from openhands.server.routes.manage_conversations import (
    app as manage_conversation_api_router,
)
from openhands.server.routes.mcp import mcp_server
from openhands.server.routes.public import app as public_api_router
from openhands.server.routes.secrets import app as secrets_router
from openhands.server.routes.security import app as security_api_router
from openhands.server.routes.settings import app as settings_router
from openhands.server.routes.trajectory import app as trajectory_router
from openhands.server.types import AppMode


def combine_lifespans(*lifespans):
    """Combine multiple FastAPI lifespans into one."""
    @contextlib.asynccontextmanager
    async def combined_lifespan(app):
        async with contextlib.AsyncExitStack() as stack:
            for lifespan in lifespans:
                await stack.enter_async_context(lifespan(app))
            yield

    return combined_lifespan


def create_openhands_app(
    context_factory: Optional[Callable[[], ServerContext]] = None,
    include_oss_routes: bool = True,
    include_mcp: bool = True,
    custom_lifespan: Optional[Callable] = None,
    title: str = 'OpenHands',
    description: str = 'OpenHands: Code Less, Make More',
) -> FastAPI:
    """Create a FastAPI application with OpenHands routes and configurable dependencies.
    
    This factory function allows external repositories to create OpenHands applications
    with their own context implementations and configuration, without relying on
    global variables or environment variable configuration.
    
    Args:
        context_factory: Factory function to create ServerContext instances.
                        If None, uses DefaultServerContext.
        include_oss_routes: Whether to include OSS-specific routes (like git).
        include_mcp: Whether to include MCP (Model Context Protocol) routes.
        custom_lifespan: Custom lifespan function for the FastAPI app.
        title: Title for the FastAPI app.
        description: Description for the FastAPI app.
    
    Returns:
        FastAPI: Configured FastAPI application with OpenHands routes.
    
    Example:
        # Basic usage with default context
        app = create_openhands_app()
        
        # Custom context for multi-tenant SaaS
        def create_saas_context():
            return SaaSServerContext(tenant_id='default')
        
        app = create_openhands_app(
            context_factory=create_saas_context,
            include_oss_routes=False
        )
        
        # External repo extending OpenHands
        from my_extension import MyServerContext, my_lifespan
        
        app = create_openhands_app(
            context_factory=lambda: MyServerContext(),
            custom_lifespan=my_lifespan
        )
    """
    # Import default context here to avoid import-time dependencies
    from openhands.server.context.default_server_context import DefaultServerContext
    
    # Use provided context factory or default
    if context_factory is None:
        context_factory = DefaultServerContext
    
    # Create a context instance to get configuration
    context = context_factory()
    server_config = context.get_server_config()
    conversation_manager = context.get_conversation_manager()
    
    # Build lifespan functions
    lifespans = []
    
    # Add conversation manager lifespan
    @asynccontextmanager
    async def conversation_lifespan(app: FastAPI) -> AsyncIterator[None]:
        async with conversation_manager:
            yield
    
    lifespans.append(conversation_lifespan)
    
    # Add MCP lifespan if requested
    if include_mcp:
        mcp_app = mcp_server.http_app(path='/mcp')
        lifespans.append(mcp_app.lifespan)
    
    # Add custom lifespan if provided
    if custom_lifespan:
        lifespans.append(custom_lifespan)
    
    # Create routes list
    routes = []
    if include_mcp:
        routes.append(Mount(path='/mcp', app=mcp_app))
    
    # Create FastAPI app
    app = FastAPI(
        title=title,
        description=description,
        version=__version__,
        lifespan=combine_lifespans(*lifespans) if lifespans else None,
        routes=routes,
    )
    
    # Add exception handlers
    @app.exception_handler(AuthenticationError)
    async def authentication_error_handler(request: Request, exc: AuthenticationError):
        return JSONResponse(
            status_code=401,
            content=str(exc),
        )
    
    # Override the context dependency for all routes
    # This is the key: we inject our context factory into the dependency system
    from openhands.server.context.context_provider import get_server_context
    
    async def custom_get_server_context(request: Request) -> ServerContext:
        """Custom context provider that uses our factory."""
        # Check if context is already cached on the request
        context = getattr(request.state, 'server_context', None)
        if context:
            return context
        
        # Create new context instance using our factory
        context = context_factory()
        
        # Cache on request for subsequent use
        request.state.server_context = context
        return context
    
    # Override the dependency
    app.dependency_overrides[get_server_context] = custom_get_server_context
    
    # Include all the standard OpenHands routes
    app.include_router(public_api_router)
    app.include_router(files_api_router)
    app.include_router(security_api_router)
    app.include_router(feedback_api_router)
    app.include_router(conversation_api_router)
    app.include_router(manage_conversation_api_router)
    app.include_router(settings_router)
    app.include_router(secrets_router)
    
    # Conditionally include OSS routes based on server config
    if include_oss_routes and server_config.app_mode == AppMode.OSS:
        app.include_router(git_api_router)
    
    app.include_router(trajectory_router)
    add_health_endpoints(app)
    
    return app


# For backward compatibility, create the default app
def create_default_app() -> FastAPI:
    """Create the default OpenHands FastAPI app.
    
    This is equivalent to the old app.py behavior but using the factory pattern.
    Used for backward compatibility.
    """
    return create_openhands_app()