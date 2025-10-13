"""MCP Proxy module for OpenHands."""

# Tolerant import so platforms without MCP deps (e.g., Windows) don't crash at import time
try:
    from openhands.runtime.mcp.proxy.manager import MCPProxyManager
except Exception:  # noqa: BLE001 - broad to avoid hard crash on any import error

    class MCPProxyManager:  # type: ignore[no-redef]
        def __init__(self, *args, **kwargs):
            pass

        def initialize(self):
            pass

        async def mount_to_app(self, *args, **kwargs):
            pass


__all__ = ['MCPProxyManager']
