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

from openhands.core.config.mcp_config import MCPStdioServerConfig

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
        self.auth_enabled = auth_enabled
        self.api_key = api_key
        self.proxy: Optional[FastMCP] = None
        # Initialize with a valid configuration format for FastMCP
        self.config: dict[str, Any] = {
            'mcpServers': {},
        }

        # Configure FastMCP logger
        if logger_level is not None:
            fastmcp_logger.setLevel(logger_level)

    def initialize(self) -> None:
        """
        Initialize the FastMCP proxy with the current configuration.
        """
        if len(self.config['mcpServers']) == 0:
            logger.info(
                f"No MCP servers configured for FastMCP Proxy, skipping initialization."
            )
            return None

        # Create a new proxy with the current configuration
        self.proxy = FastMCP.as_proxy(
            self.config,
            auth_enabled=self.auth_enabled,
            api_key=self.api_key,
        )

        logger.info(f"FastMCP Proxy initialized successfully")

    async def shutdown(self) -> None:
        """
        Shutdown the FastMCP proxy.
        """
        if self.proxy:
            try:
                logger.info(f"Shutting down FastMCP Proxy...")
                await self.proxy.shutdown()
                logger.info(f"FastMCP Proxy shutdown successfully")
            except Exception as e:
                logger.error(
                    f"Error shutting down FastMCP Proxy: {e}",
                    exc_info=True,
                )
            finally:
                self.proxy = None
        else:
            logger.info(f"FastMCP Proxy instance not found for shutdown")

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
        if len(self.config['mcpServers']) == 0:
            logger.info(
                f"No MCP servers configured for FastMCP Proxy, skipping mount."
            )
            return

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
            f"Mounted FastMCP Proxy SSE app at root path with allowed origins: {allow_origins}"
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
        self,
        app: FastAPI,
        stdio_servers: list[MCPStdioServerConfig],
        allow_origins: Optional[list[str]] = None,
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
        tools = {
            t.name: t.model_dump()
            for t in stdio_servers
        }
        self.config['mcpServers'] = tools

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
