from typing import Annotated
from pydantic import Field
from fastmcp import FastMCP
from fastmcp.server.dependencies import get_http_request
from openhands.integrations.github.github_service import GithubServiceImpl
from openhands.integrations.gitlab.gitlab_service import GitLabServiceImpl
from openhands.integrations.provider import ProviderToken
from openhands.integrations.service_types import ProviderType
from openhands.server.user_auth import get_access_token, get_provider_tokens, get_user_id


mcp_server = FastMCP('mcp')


@mcp_server.tool()
async def create_pr(
    repo_name: Annotated[
        str, Field(description='GitHub repository ({{owner}}/{{repo}})')
    ],
    source_branch: Annotated[str, Field(description='Source branch on repo')],
    target_branch: Annotated[str, Field(description='Target branch on repo')],
    title: Annotated[str, Field(description='PR Title')],
    body: Annotated[str | None, Field(description='PR body')]
) -> str:
    """Open a draft PR in GitHub"""
    
    request = get_http_request()
    provider_tokens = await get_provider_tokens(request)
    access_token = await get_access_token(request)
    user_id = await get_user_id(request)

    github_token = provider_tokens.get(ProviderType.GITHUB, ProviderToken()) if provider_tokens else ProviderToken()

    github_service = GithubServiceImpl(
        user_id=github_token.user_id,
        external_auth_id=user_id,
        external_auth_token=access_token,
        token=github_token.token,
        base_domain=github_token.host
    )

    try:
        response = await github_service.create_pr(
            repo_name=repo_name,
            source_branch=source_branch,
            target_branch=target_branch,
            title=title,
            body=body
        )
    except Exception as e:
        response = str(e)

    return response



@mcp_server.tool()
async def create_mr(
    id: Annotated[
        int | str, Field(description='GitLab repository (ID or URL-encoded path of the project)')
    ],
    source_branch: Annotated[str, Field(description='Source branch on repo')],
    target_branch: Annotated[str, Field(description='Target branch on repo')],
    title: Annotated[str, Field(description='MR Title')],
    description: Annotated[str | None, Field(description='MR description')]
) -> str:
    """Open a draft PR in GitHub"""
    
    request = get_http_request()
    provider_tokens = await get_provider_tokens(request)
    access_token = await get_access_token(request)
    user_id = await get_user_id(request)

    github_token = provider_tokens.get(ProviderType.GITLAB, ProviderToken()) if provider_tokens else ProviderToken()

    github_service = GitLabServiceImpl(
        user_id=github_token.user_id,
        external_auth_id=user_id,
        external_auth_token=access_token,
        token=github_token.token,
        base_domain=github_token.host
    )

    try:
        response = await github_service.create_mr(
            id=id,
            source_branch=source_branch,
            target_branch=target_branch,
            title=title,
            description=description,
        )
    except Exception as e:
        response = str(e)

    return response



