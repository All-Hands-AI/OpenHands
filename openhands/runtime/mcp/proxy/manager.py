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
        # mcp_app = self.proxy.http_app(path='/shttp')
        mcp_app = self.proxy.http_app(path='/sse', transport='sse')
        app.mount('/mcp', mcp_app)

        # Remove any existing mounts at root path
        if '/mcp' in app.routes:
            app.routes.remove('/mcp')

        app.mount('/', mcp_app)
        logger.info(f"Mounted FastMCP Proxy app at /mcp")


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

        del self.proxy
        self.proxy = None

        # Initialize a new proxy
        self.initialize()

        # Mount the new proxy to the app
        await self.mount_to_app(app, allow_origins)
