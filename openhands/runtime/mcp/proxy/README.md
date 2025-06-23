# MCP Proxy Manager

This module provides a manager class for handling FastMCP proxy instances in OpenHands, including initialization, configuration, and mounting to FastAPI applications.

## Overview

The `MCPProxyManager` class encapsulates all the functionality related to creating, configuring, and managing FastMCP proxy instances. It simplifies the process of:

1. Initializing a FastMCP proxy
2. Configuring the proxy with tools
3. Mounting the proxy to a FastAPI application
4. Updating the proxy configuration
5. Shutting down the proxy

## Usage

### Basic Usage

```python
from openhands.runtime.mcp.proxy import MCPProxyManager
from fastapi import FastAPI

# Create a FastAPI app
app = FastAPI()

# Create a proxy manager
proxy_manager = MCPProxyManager(
    name="MyProxyServer",
    auth_enabled=True,
    api_key="my-api-key"
)

# Initialize the proxy
proxy_manager.initialize()

# Mount the proxy to the app
await proxy_manager.mount_to_app(app, allow_origins=["*"])

# Update the tools configuration
tools = [
    {
        "name": "my_tool",
        "description": "My tool description",
        "parameters": {...}
    }
]
proxy_manager.update_tools(tools)

# Update and remount the proxy
await proxy_manager.update_and_remount(app, tools, allow_origins=["*"])

# Shutdown the proxy
await proxy_manager.shutdown()
```

### In-Memory Configuration

The `MCPProxyManager` maintains the configuration in-memory, eliminating the need for file-based configuration. This makes it easier to update the configuration and reduces the complexity of the code.

## Benefits

1. **Simplified API**: The `MCPProxyManager` provides a simple and intuitive API for managing FastMCP proxies.
2. **In-Memory Configuration**: Configuration is maintained in-memory, eliminating the need for file I/O operations.
3. **Improved Error Handling**: The manager provides better error handling and logging for proxy operations.
4. **Cleaner Code**: By encapsulating proxy-related functionality in a dedicated class, the code is more maintainable and easier to understand.

## Implementation Details

The `MCPProxyManager` uses the `FastMCP.as_proxy()` method to create a proxy server. It manages the lifecycle of the proxy, including initialization, configuration updates, and shutdown.

When updating the tools configuration, the manager creates a new proxy with the updated configuration and remounts it to the FastAPI application, ensuring that the proxy is always up-to-date with the latest configuration.
