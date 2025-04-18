from abc import ABC, abstractmethod
from typing import Dict, Optional

from mcp import ClientSession
from mcp.types import CallToolResult, TextContent, Tool


class MCPClientTool(Tool):
    """Represents a tool proxy that can be called on the MCP server from the client side."""

    session: Optional[ClientSession] = None

    class Config:
        arbitrary_types_allowed = True

    def to_param(self) -> Dict:
        """Convert tool to function call format."""
        return {
            'type': 'function',
            'function': {
                'name': self.name,
                'description': self.description,
                'parameters': self.inputSchema,
            },
        }

    async def execute(self, **kwargs) -> CallToolResult:
        """Execute the tool by making a remote call to the MCP server."""
        if not self.session:
            return CallToolResult(
                content=[TextContent(text='Not connected to MCP server', type='text')],
                isError=True,
            )

        try:
            result = await self.session.call_tool(self.name, kwargs)
            return result
        except Exception as e:
            return CallToolResult(
                content=[
                    TextContent(text=f'Error executing tool: {str(e)}', type='text')
                ],
                isError=True,
            )
