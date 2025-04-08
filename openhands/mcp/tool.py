from abc import ABC, abstractmethod
from typing import Dict, Optional

from mcp import ClientSession
from mcp.types import CallToolResult, TextContent, Tool


class BaseTool(ABC, Tool):
    @classmethod
    def postfix(cls) -> str:
        return '_mcp_tool_call'

    class Config:
        arbitrary_types_allowed = True

    @abstractmethod
    async def execute(self, **kwargs) -> CallToolResult:
        """Execute the tool with given parameters."""

    def to_param(self) -> Dict:
        """Convert tool to function call format."""
        return {
            'type': 'function',
            'function': {
                'name': self.name + self.postfix(),
                'description': self.description,
                'parameters': self.inputSchema,
            },
        }


class MCPClientTool(BaseTool):
    """Represents a tool proxy that can be called on the MCP server from the client side."""

    session: Optional[ClientSession] = None

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
