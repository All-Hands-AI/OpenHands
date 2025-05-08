from fastmcp import FastMCP, Context
from typing import Annotated
from pydantic import Field


mcp_server = FastMCP("mcp")


@mcp_server.tool()
def create_pr(
    repo_name: Annotated[str, Field(description="GitHub repository ({{owner}}/{{repo}})")], 
    source_branch: Annotated[str, Field(description="Source branch on repo")], 
    target_branch: Annotated[str, Field(description="Target branch on repo")],
    ctx: Context
) -> str:
    """Open a PR in GitHub"""
    request = ctx.get_http_request()
    print(request)

    return "pr was created successfully"