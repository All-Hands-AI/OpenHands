import os
import shutil
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from types import MappingProxyType
from typing import cast

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
    ProviderType,
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
    created_at: datetime
    git_provider: ProviderType


def _get_file_creation_time(repo_dir: Path, file_path: Path) -> datetime:
    """Get the creation time of a file from Git history.

    Args:
        repo_dir: The root directory of the Git repository
        file_path: The path to the file relative to the repository root

    Returns:
        datetime: The timestamp when the file was first added to the repository
    """
    try:
        # Get the relative path from the repository root
        relative_path = file_path.relative_to(repo_dir)

        # Use git log to get the first commit that added this file
        # --follow: follow renames and moves
        # --reverse: show commits in reverse chronological order (oldest first)
        # --format=%ct: show commit timestamp in Unix format
        # -1: limit to 1 result (the first commit)
        cmd = [
            'git',
            'log',
            '--follow',
            '--reverse',
            '--format=%ct',
            '-1',
            str(relative_path),
        ]

        result = subprocess.run(
            cmd, cwd=repo_dir, capture_output=True, text=True, timeout=10
        )

        if result.returncode == 0 and result.stdout.strip():
            # Parse Unix timestamp and convert to datetime
            timestamp = int(result.stdout.strip())
            return datetime.fromtimestamp(timestamp)
        else:
            logger.warning(
                f'Failed to get creation time for {relative_path}: {result.stderr}'
            )
            # Fallback to current time if git log fails
            return datetime.now()

    except Exception as e:
        logger.warning(f'Error getting creation time for {file_path}: {str(e)}')
        # Fallback to current time if there's any error
        return datetime.now()


async def _verify_repository_access(
    repository_name: str,
    provider_tokens: PROVIDER_TOKEN_TYPE | None,
    access_token: SecretStr | None,
    user_id: str | None,
) -> Repository:
    """Verify repository access and return repository information.

    Args:
        repository_name: Repository name in the format 'owner/repo'
        provider_tokens: Provider tokens for authentication
        access_token: Access token for external authentication
        user_id: User ID for authentication

    Returns:
        Repository object with provider information

    Raises:
        AuthenticationError: If authentication fails
    """
    provider_handler = ProviderHandler(
        provider_tokens=provider_tokens
        or cast(PROVIDER_TOKEN_TYPE, MappingProxyType({})),
        external_auth_token=access_token,
        external_auth_id=user_id,
    )

    repository = await provider_handler.verify_repo_provider(repository_name)
    logger.info(
        f'Detected git provider: {repository.git_provider} for repository: {repository_name}'
    )
    return repository


def _clone_repository(remote_url: str, repository_name: str) -> Path:
    """Clone repository to temporary directory.

    Args:
        remote_url: Authenticated git URL for cloning
        repository_name: Repository name for error messages

    Returns:
        Path to the cloned repository directory

    Raises:
        RuntimeError: If cloning fails
    """
    temp_dir = tempfile.mkdtemp()
    repo_dir = Path(temp_dir) / 'repo'

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
        # Clean up on failure
        shutil.rmtree(temp_dir, ignore_errors=True)
        error_msg = f'Failed to clone repository: {result.stderr}'
        logger.error(f'Failed to clone repository {repository_name}: {result.stderr}')
        raise RuntimeError(error_msg)

    return repo_dir


def _extract_repo_name(repository_name: str) -> str:
    """Extract the actual repository name from the full repository path.

    Args:
        repository_name: Repository name in format 'owner/repo' or 'domain/owner/repo'

    Returns:
        The actual repository name (last part after the last '/')
    """
    return repository_name.split('/')[-1]


def _process_microagents(
    repo_dir: Path,
    repository_name: str,
    git_provider: ProviderType,
) -> list[MicroagentResponse]:
    """Process microagents from the cloned repository.

    Args:
        repo_dir: Path to the cloned repository directory
        repository_name: Repository name for logging
        git_provider: Git provider type

    Returns:
        List of microagents found in the repository
    """
    # Extract the actual repository name from the full path
    actual_repo_name = _extract_repo_name(repository_name)

    # Determine the microagents directory based on git provider and repository name
    if git_provider != ProviderType.GITLAB and actual_repo_name == '.openhands':
        # For non-GitLab providers with repository name ".openhands", scan "microagents" folder
        microagents_dir = repo_dir / 'microagents'
    elif git_provider == ProviderType.GITLAB and actual_repo_name == 'openhands-config':
        # For GitLab with repository name "openhands-config", scan "microagents" folder
        microagents_dir = repo_dir / 'microagents'
    else:
        # Default behavior: look for .openhands/microagents directory
        microagents_dir = repo_dir / '.openhands' / 'microagents'

    if not microagents_dir.exists():
        logger.info(
            f'No microagents directory found in {repository_name} at {microagents_dir}'
        )
        return []

    # Load microagents from the directory
    repo_agents, knowledge_agents = load_microagents_from_dir(microagents_dir)

    # Prepare response
    microagents = []

    # Add repo microagents
    for name, r_agent in repo_agents.items():
        # Get the actual creation time from Git
        agent_file_path = Path(r_agent.source)
        created_at = _get_file_creation_time(repo_dir, agent_file_path)

        microagents.append(
            MicroagentResponse(
                name=name,
                type='repo',
                content=r_agent.content,
                triggers=[],
                inputs=r_agent.metadata.inputs,
                tools=(
                    [server.name for server in r_agent.metadata.mcp_tools.stdio_servers]
                    if r_agent.metadata.mcp_tools
                    else []
                ),
                created_at=created_at,
                git_provider=git_provider,
            )
        )

    # Add knowledge microagents
    for name, k_agent in knowledge_agents.items():
        # Get the actual creation time from Git
        agent_file_path = Path(k_agent.source)
        created_at = _get_file_creation_time(repo_dir, agent_file_path)

        microagents.append(
            MicroagentResponse(
                name=name,
                type='knowledge',
                content=k_agent.content,
                triggers=k_agent.triggers,
                inputs=k_agent.metadata.inputs,
                tools=(
                    [server.name for server in k_agent.metadata.mcp_tools.stdio_servers]
                    if k_agent.metadata.mcp_tools
                    else []
                ),
                created_at=created_at,
                git_provider=git_provider,
            )
        )

    logger.info(f'Found {len(microagents)} microagents in {repository_name}')
    return microagents


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
    """Scan the microagents directory of a repository and return the list of microagents.

    The microagents directory location depends on the git provider and actual repository name:
    - If git provider is not GitLab and actual repository name is ".openhands": scans "microagents" folder
    - If git provider is GitLab and actual repository name is "openhands-config": scans "microagents" folder
    - Otherwise: scans ".openhands/microagents" folder

    Args:
        repository_name: Repository name in the format 'owner/repo' or 'domain/owner/repo'
        provider_tokens: Provider tokens for authentication
        access_token: Access token for external authentication
        user_id: User ID for authentication

    Returns:
        List of microagents found in the repository's microagents directory
    """
    repo_dir = None

    try:
        # Verify repository access and get provider information
        repository = await _verify_repository_access(
            repository_name, provider_tokens, access_token, user_id
        )

        # Construct authenticated git URL using provider handler
        provider_handler = ProviderHandler(
            provider_tokens=provider_tokens
            or cast(PROVIDER_TOKEN_TYPE, MappingProxyType({})),
            external_auth_token=access_token,
            external_auth_id=user_id,
        )
        remote_url = await provider_handler.get_authenticated_git_url(repository_name)

        # Clone repository
        repo_dir = _clone_repository(remote_url, repository_name)

        # Process microagents
        microagents = _process_microagents(
            repo_dir, repository_name, repository.git_provider
        )

        return microagents

    except AuthenticationError as e:
        logger.info(
            f'Returning 401 Unauthorized - Authentication error for user_id: {user_id}, error: {str(e)}'
        )
        return JSONResponse(
            content=str(e),
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    except RuntimeError as e:
        return JSONResponse(
            content=str(e),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    except Exception as e:
        logger.error(
            f'Error scanning repository {repository_name}: {str(e)}', exc_info=True
        )
        return JSONResponse(
            content=f'Error scanning repository: {str(e)}',
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    finally:
        # Clean up temporary directory
        if repo_dir and repo_dir.parent.exists():
            shutil.rmtree(repo_dir.parent, ignore_errors=True)
