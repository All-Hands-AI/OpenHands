from typing import Annotated
from pydantic import Field
from fastmcp import FastMCP
from fastmcp.server.dependencies import get_http_request
from openhands.server.user_auth import get_provider_tokens


mcp_server = FastMCP('mcp')


@mcp_server.tool()
async def create_pr(
    repo_name: Annotated[
        str, Field(description='GitHub repository ({{owner}}/{{repo}})')
    ],
    source_branch: Annotated[str, Field(description='Source branch on repo')],
    target_branch: Annotated[str, Field(description='Target branch on repo')],
) -> str:
    """Open a PR in GitHub"""
    
    request = get_http_request()
    provider_tokens = await get_provider_tokens(request)

    return "pr was created successfully"
