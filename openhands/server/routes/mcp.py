# from fastmcp import FastMCP, Context
from typing import Annotated

from fastmcp import Context, FastMCP
from pydantic import Field

from mcp.server.fastmcp.server import FastMCP, Context


mcp_server = FastMCP('mcp')


@mcp_server.tool()
def create_pr(
    repo_name: Annotated[
        str, Field(description='GitHub repository ({{owner}}/{{repo}})')
    ],
    source_branch: Annotated[str, Field(description='Source branch on repo')],
    target_branch: Annotated[str, Field(description='Target branch on repo')],
    ctx: Context,
) -> str:
    """Open a PR in GitHub"""
    print("starlette context", ctx)

    return "pr was created successfully"
