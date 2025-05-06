from mcp.types import Tool


class MCPClientTool(Tool):
    """
    Represents a tool proxy that can be called on the MCP server from the client side.

    This version doesn't store a session reference, as sessions are created on-demand
    by the MCPClient for each operation.
    """

    class Config:
        arbitrary_types_allowed = True

    def to_param(self) -> dict:
        """Convert tool to function call format."""
        return {
            'type': 'function',
            'function': {
                'name': self.name,
                'description': self.description,
                'parameters': self.inputSchema,
            },
        }
