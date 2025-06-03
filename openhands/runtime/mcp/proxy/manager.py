"""
MCP Proxy Manager for OpenHands.

This module provides a manager class for handling FastMCP proxy instances,
including initialization, configuration, and mounting to FastAPI applications.
"""

import logging
from typing import Any, Optional

from fastapi import FastAPI
from fastmcp import FastMCP
from fastmcp.utilities.logging import get_logger as fastmcp_get_logger

logger = logging.getLogger(__name__)
fastmcp_logger = fastmcp_get_logger('fastmcp')


class MCPProxyManager:
    """
    Manager for FastMCP proxy instances.

    This class encapsulates all the functionality related to creating, configuring,
    and managing FastMCP proxy instances, including mounting them to FastAPI applications.
    """

    def __init__(
        self,
        name: str = 'OpenHandsActionExecutionProxy',
        auth_enabled: bool = False,
        api_key: Optional[str] = None,
        logger_level: Optional[int] = None,
    ):
        """
        Initialize the MCP Proxy Manager.

        Args:
            name: Name of the proxy server
            auth_enabled: Whether authentication is enabled
            api_key: API key for authentication (required if auth_enabled is True)
            logger_level: Logging level for the FastMCP logger
        """
        self.name = name
        self.auth_enabled = auth_enabled
        self.api_key = api_key
        self.proxy: Optional[FastMCP] = None
        self.config: dict[str, Any] = {'mcpServers': {'default': {}}, 'tools': []}

        # Configure FastMCP logger
        if logger_level is not None:
            fastmcp_logger.setLevel(logger_level)

    def initialize(self) -> FastMCP:
        """
        Initialize the FastMCP proxy with the current configuration.

        Returns:
            The initialized FastMCP proxy instance
        """
        logger.info(f"Initializing FastMCP Proxy '{self.name}'...")

        # Create a new proxy with the current configuration
        self.proxy = FastMCP.as_proxy(
            self.config,
            name=self.name,
            auth_enabled=self.auth_enabled,
            api_key=self.api_key,
        )

        logger.info(f"FastMCP Proxy '{self.name}' initialized successfully")
        return self.proxy

    async def shutdown(self) -> None:
        """
        Shutdown the FastMCP proxy.
        """
        if self.proxy:
            try:
                logger.info(f"Shutting down FastMCP Proxy '{self.name}'...")
                await self.proxy.shutdown()
                logger.info(f"FastMCP Proxy '{self.name}' shutdown successfully")
            except Exception as e:
                logger.error(
                    f"Error shutting down FastMCP Proxy '{self.name}': {e}",
                    exc_info=True,
                )
            finally:
                self.proxy = None
        else:
            logger.info(f"FastMCP Proxy '{self.name}' instance not found for shutdown")

    def update_tools(self, tools: list[Any]) -> None:
        """
        Update the tools configuration.

        Args:
            tools: List of tool configurations
        """
        logger.info(f"Updating tools for FastMCP Proxy '{self.name}'")
        self.config['tools'] = tools

    async def get_sse_server_app(
        self, allow_origins: Optional[list[str]] = None
    ) -> FastAPI:
        """
        Get the SSE server app for the proxy.

        Args:
            allow_origins: List of allowed origins for CORS

        Returns:
            FastAPI application for the SSE server
        """
        if not self.proxy:
            raise ValueError('FastMCP Proxy is not initialized')

        origins = ['*'] if allow_origins is None else allow_origins

        return await self.proxy.get_sse_server_app(
            allow_origins=origins, include_lifespan=False
        )

    async def mount_to_app(
        self, app: FastAPI, allow_origins: Optional[list[str]] = None
    ) -> None:
        """
        Mount the SSE server app to a FastAPI application.

        Args:
            app: FastAPI application to mount to
            allow_origins: List of allowed origins for CORS
        """
        if not self.proxy:
            raise ValueError('FastMCP Proxy is not initialized')

        # Get the SSE app
        sse_app = await self.get_sse_server_app(allow_origins)

        # Check for route conflicts
        main_app_routes = {route.path for route in app.routes}
        sse_app_routes = {route.path for route in sse_app.routes}
        conflicts = main_app_routes.intersection(sse_app_routes)

        if conflicts:
            logger.warning(f'Route conflicts detected: {conflicts}')

        # Remove any existing mounts at root path
        self._remove_existing_mounts(app)

        # Mount the SSE app
        app.mount('/', sse_app)
        logger.info(
            f"Mounted FastMCP Proxy '{self.name}' SSE app at root path with allowed origins: {allow_origins}"
        )

        # Additional debug logging
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug('Main app routes:')
            for route in main_app_routes:
                logger.debug(f'  {route}')
            logger.debug('FastMCP SSE server app routes:')
            for route in sse_app_routes:
                logger.debug(f'  {route}')

    async def update_and_remount(
        self, app: FastAPI, tools: list[Any], allow_origins: Optional[list[str]] = None
    ) -> None:
        """
        Update the tools configuration and remount the proxy to the app.

        This is a convenience method that combines updating the tools,
        shutting down the existing proxy, initializing a new one, and
        mounting it to the app.

        Args:
            app: FastAPI application to mount to
            tools: List of tool configurations
            allow_origins: List of allowed origins for CORS
        """
        # Update the tools configuration
        self.update_tools(tools)

        # Shutdown the existing proxy
        await self.shutdown()

        # Initialize a new proxy
        self.initialize()

        # Mount the new proxy to the app
        await self.mount_to_app(app, allow_origins)

    def _remove_existing_mounts(self, app: FastAPI) -> None:
        """
        Remove any existing mounts at the root path.

        Args:
            app: FastAPI application to remove mounts from
        """
        for route in list(app.routes):
            if getattr(route, 'path', '') == '/':
                app.routes.remove(route)
