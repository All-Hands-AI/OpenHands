from mcp.server.fastmcp import FastMCP


mcp_server = FastMCP("mcp")


@mcp_server.tool()
def add(a: int, b: int) -> int:
    """Adds two numbers."""
    return a + b