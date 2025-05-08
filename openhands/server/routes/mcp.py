from typing import Annotated

from fastmcp import Context, FastMCP
from pydantic import Field

from openhands.core.logger import openhands_logger as logger

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
    try:
        request = ctx.get_http_request()
        logger.info(f'Request context available: {request}')
    except Exception as e:
        logger.warning(f'Request context not available: {e}')
        logger.info(
            f'Creating PR without request context: {repo_name}, {source_branch} -> {target_branch}'
        )
        # Continue with PR creation even without request context

    # Implement PR creation logic here
    # This is a placeholder implementation
    logger.info(f'Creating PR for {repo_name}: {source_branch} -> {target_branch}')

    return (
        f'PR created successfully for {repo_name}: {source_branch} -> {target_branch}'
    )
