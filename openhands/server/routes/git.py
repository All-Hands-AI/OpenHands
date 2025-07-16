import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, SecretStr

from openhands.core.logger import openhands_logger as logger
from openhands.integrations.provider import (
    PROVIDER_TOKEN_TYPE,
    ProviderHandler,
)
from openhands.integrations.service_types import (
    AuthenticationError,
    Branch,
    Repository,
    SuggestedTask,
    UnknownException,
    User,
)
from openhands.microagent import load_microagents_from_dir
from openhands.microagent.types import InputMetadata
from openhands.server.dependencies import get_dependencies
from openhands.server.shared import server_config
from openhands.server.user_auth import (
    get_access_token,
    get_provider_tokens,
    get_user_id,
)

app = APIRouter(prefix='/api/user', dependencies=get_dependencies())


@app.get('/repositories', response_model=list[Repository])
async def get_user_repositories(
    sort: str = 'pushed',
    provider_tokens: PROVIDER_TOKEN_TYPE | None = Depends(get_provider_tokens),
    access_token: SecretStr | None = Depends(get_access_token),
    user_id: str | None = Depends(get_user_id),
) -> list[Repository] | JSONResponse:
    if provider_tokens:
        client = ProviderHandler(
            provider_tokens=provider_tokens,
            external_auth_token=access_token,
            external_auth_id=user_id,
        )

        try:
            return await client.get_repositories(sort, server_config.app_mode)

        except AuthenticationError as e:
            logger.info(
                f'Returning 401 Unauthorized - Authentication error for user_id: {user_id}, error: {str(e)}'
            )
            return JSONResponse(
                content=str(e),
                status_code=status.HTTP_401_UNAUTHORIZED,
            )

        except UnknownException as e:
            return JSONResponse(
                content=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    logger.info(
        f'Returning 401 Unauthorized - Git provider token required for user_id: {user_id}'
    )
    return JSONResponse(
        content='Git provider token required. (such as GitHub).',
        status_code=status.HTTP_401_UNAUTHORIZED,
    )


@app.get('/info', response_model=User)
async def get_user(
    provider_tokens: PROVIDER_TOKEN_TYPE | None = Depends(get_provider_tokens),
    access_token: SecretStr | None = Depends(get_access_token),
    user_id: str | None = Depends(get_user_id),
) -> User | JSONResponse:
    if provider_tokens:
        client = ProviderHandler(
            provider_tokens=provider_tokens, external_auth_token=access_token
        )

        try:
            user: User = await client.get_user()
            return user

        except AuthenticationError as e:
            logger.info(
                f'Returning 401 Unauthorized - Authentication error for user_id: {user_id}, error: {str(e)}'
            )
            return JSONResponse(
                content=str(e),
                status_code=status.HTTP_401_UNAUTHORIZED,
            )

        except UnknownException as e:
            return JSONResponse(
                content=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    logger.info(
        f'Returning 401 Unauthorized - Git provider token required for user_id: {user_id}'
    )
    return JSONResponse(
        content='Git provider token required. (such as GitHub).',
        status_code=status.HTTP_401_UNAUTHORIZED,
    )


@app.get('/search/repositories', response_model=list[Repository])
async def search_repositories(
    query: str,
    per_page: int = 5,
    sort: str = 'stars',
    order: str = 'desc',
    provider_tokens: PROVIDER_TOKEN_TYPE | None = Depends(get_provider_tokens),
    access_token: SecretStr | None = Depends(get_access_token),
    user_id: str | None = Depends(get_user_id),
) -> list[Repository] | JSONResponse:
    if provider_tokens:
        client = ProviderHandler(
            provider_tokens=provider_tokens, external_auth_token=access_token
        )
        try:
            repos: list[Repository] = await client.search_repositories(
                query, per_page, sort, order
            )
            return repos

        except AuthenticationError as e:
            return JSONResponse(
                content=str(e),
                status_code=status.HTTP_401_UNAUTHORIZED,
            )

        except UnknownException as e:
            return JSONResponse(
                content=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    logger.info(
        f'Returning 401 Unauthorized - GitHub token required for user_id: {user_id}'
    )
    return JSONResponse(
        content='GitHub token required.',
        status_code=status.HTTP_401_UNAUTHORIZED,
    )


@app.get('/suggested-tasks', response_model=list[SuggestedTask])
async def get_suggested_tasks(
    provider_tokens: PROVIDER_TOKEN_TYPE | None = Depends(get_provider_tokens),
    access_token: SecretStr | None = Depends(get_access_token),
    user_id: str | None = Depends(get_user_id),
) -> list[SuggestedTask] | JSONResponse:
    """Get suggested tasks for the authenticated user across their most recently pushed repositories.

    Returns:
    - PRs owned by the user
    - Issues assigned to the user.
    """
    if provider_tokens:
        client = ProviderHandler(
            provider_tokens=provider_tokens, external_auth_token=access_token
        )
        try:
            tasks: list[SuggestedTask] = await client.get_suggested_tasks()
            return tasks

        except AuthenticationError as e:
            return JSONResponse(
                content=str(e),
                status_code=status.HTTP_401_UNAUTHORIZED,
            )

        except UnknownException as e:
            return JSONResponse(
                content=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
    logger.info(f'Returning 401 Unauthorized - No providers set for user_id: {user_id}')

    return JSONResponse(
        content='No providers set.',
        status_code=status.HTTP_401_UNAUTHORIZED,
    )


@app.get('/repository/branches', response_model=list[Branch])
async def get_repository_branches(
    repository: str,
    provider_tokens: PROVIDER_TOKEN_TYPE | None = Depends(get_provider_tokens),
    access_token: SecretStr | None = Depends(get_access_token),
    user_id: str | None = Depends(get_user_id),
) -> list[Branch] | JSONResponse:
    """Get branches for a repository.

    Args:
        repository: The repository name in the format 'owner/repo'

    Returns:
        A list of branches for the repository
    """
    if provider_tokens:
        client = ProviderHandler(
            provider_tokens=provider_tokens, external_auth_token=access_token
        )
        try:
            branches: list[Branch] = await client.get_branches(repository)
            return branches

        except AuthenticationError as e:
            return JSONResponse(
                content=str(e),
                status_code=status.HTTP_401_UNAUTHORIZED,
            )

        except UnknownException as e:
            return JSONResponse(
                content=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    logger.info(
        f'Returning 401 Unauthorized - Git provider token required for user_id: {user_id}'
    )

    return JSONResponse(
        content='Git provider token required. (such as GitHub).',
        status_code=status.HTTP_401_UNAUTHORIZED,
    )


class MicroagentResponse(BaseModel):
    """Response model for microagents endpoint."""

    name: str
    type: str
    content: str
    triggers: list[str] = []
    inputs: list[InputMetadata] = []
    tools: list[str] = []


@app.get(
    '/repository/{repository_name:path}/microagents',
    response_model=list[MicroagentResponse],
)
async def get_repository_microagents(
    repository_name: str,
    provider_tokens: PROVIDER_TOKEN_TYPE | None = Depends(get_provider_tokens),
    access_token: SecretStr | None = Depends(get_access_token),
    user_id: str | None = Depends(get_user_id),
) -> list[MicroagentResponse] | JSONResponse:
    """Scan the .openhands/microagents directory of a repository and return the list of microagents.

    Args:
        repository_name: Repository name in the format 'owner/repo' or 'domain/owner/repo'
        provider_tokens: Provider tokens for authentication
        access_token: Access token for external authentication
        user_id: User ID for authentication

    Returns:
        List of microagents found in the repository's .openhands/microagents directory
    """
    if not provider_tokens:
        logger.info(
            f'Returning 401 Unauthorized - Git provider token required for user_id: {user_id}'
        )
        return JSONResponse(
            content='Git provider token required. (such as GitHub).',
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    try:
        # Create ProviderHandler to detect git provider and get repository info
        provider_handler = ProviderHandler(
            provider_tokens=provider_tokens,
            external_auth_token=access_token,
            external_auth_id=user_id,
        )

        # Verify repository and get provider information
        try:
            repository = await provider_handler.verify_repo_provider(repository_name)
            git_provider = repository.git_provider
            logger.info(
                f'Detected git provider: {git_provider} for repository: {repository_name}'
            )
        except AuthenticationError as e:
            logger.info(
                f'Returning 401 Unauthorized - Authentication error for user_id: {user_id}, error: {str(e)}'
            )
            return JSONResponse(
                content=str(e),
                status_code=status.HTTP_401_UNAUTHORIZED,
            )

        # Get authenticated git URL
        provider_token = provider_tokens[git_provider]
        domain = provider_token.host or _get_default_domain(git_provider)

        if provider_token.token:
            token_value = provider_token.token.get_secret_value()
            if git_provider.value == 'gitlab':
                remote_url = (
                    f'https://oauth2:{token_value}@{domain}/{repository_name}.git'
                )
            elif git_provider.value == 'bitbucket':
                if ':' in token_value:
                    # App token format: username:app_password
                    remote_url = f'https://{token_value}@{domain}/{repository_name}.git'
                else:
                    # Access token format: use x-token-auth
                    remote_url = f'https://x-token-auth:{token_value}@{domain}/{repository_name}.git'
            else:
                # GitHub
                remote_url = f'https://{token_value}@{domain}/{repository_name}.git'
        else:
            remote_url = f'https://{domain}/{repository_name}.git'

        # Create temporary directory for cloning
        temp_dir = tempfile.mkdtemp()
        repo_dir = Path(temp_dir) / 'repo'

        try:
            # Clone the repository (shallow clone for efficiency)
            clone_cmd = ['git', 'clone', '--depth', '1', remote_url, str(repo_dir)]

            # Set environment variable to avoid interactive prompts
            env = os.environ.copy()
            env['GIT_TERMINAL_PROMPT'] = '0'

            result = subprocess.run(
                clone_cmd,
                capture_output=True,
                text=True,
                env=env,
                timeout=30,  # 30 second timeout
            )

            if result.returncode != 0:
                logger.error(
                    f'Failed to clone repository {repository_name}: {result.stderr}'
                )
                return JSONResponse(
                    content=f'Failed to clone repository: {result.stderr}',
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            # Look for .openhands/microagents directory
            microagents_dir = repo_dir / '.openhands' / 'microagents'

            if not microagents_dir.exists():
                logger.info(
                    f'No .openhands/microagents directory found in {repository_name}'
                )
                return []

            # Load microagents from the directory
            repo_agents, knowledge_agents = load_microagents_from_dir(microagents_dir)

            # Prepare response
            microagents = []

            # Add repo microagents
            for name, r_agent in repo_agents.items():
                microagents.append(
                    MicroagentResponse(
                        name=name,
                        type='repo',
                        content=r_agent.content,
                        triggers=[],
                        inputs=r_agent.metadata.inputs,
                        tools=(
                            [
                                server.name
                                for server in r_agent.metadata.mcp_tools.stdio_servers
                            ]
                            if r_agent.metadata.mcp_tools
                            else []
                        ),
                    )
                )

            # Add knowledge microagents
            for name, k_agent in knowledge_agents.items():
                microagents.append(
                    MicroagentResponse(
                        name=name,
                        type='knowledge',
                        content=k_agent.content,
                        triggers=k_agent.triggers,
                        inputs=k_agent.metadata.inputs,
                        tools=(
                            [
                                server.name
                                for server in k_agent.metadata.mcp_tools.stdio_servers
                            ]
                            if k_agent.metadata.mcp_tools
                            else []
                        ),
                    )
                )

            logger.info(f'Found {len(microagents)} microagents in {repository_name}')
            return microagents

        finally:
            # Clean up temporary directory
            shutil.rmtree(temp_dir, ignore_errors=True)

    except Exception as e:
        logger.error(
            f'Error scanning repository {repository_name}: {str(e)}', exc_info=True
        )
        return JSONResponse(
            content=f'Error scanning repository: {str(e)}',
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


def _get_default_domain(git_provider):
    """Get the default domain for a git provider."""
    from openhands.integrations.service_types import ProviderType

    domain_map = {
        ProviderType.GITHUB: 'github.com',
        ProviderType.GITLAB: 'gitlab.com',
        ProviderType.BITBUCKET: 'bitbucket.org',
    }
    return domain_map.get(git_provider, 'github.com')
