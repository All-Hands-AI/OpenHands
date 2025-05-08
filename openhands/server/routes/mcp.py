from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp import Context


mcp_server = FastMCP("mcp")


@mcp_server.tool()
def add(a: int, b: int) -> int:
    """Adds two numbers."""
    return a + b



@mcp_server.tool()
def create_pr(source_branch: str, target_branch: str, ctx: Context):
    """Open a PR in GitHub"""

    pass