import base64
from datetime import datetime
from types import MappingProxyType
from typing import cast

import httpx
from fastapi import APIRouter, Depends, Query, status
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
    """Response model for microagents endpoint.

    Note: This model only includes basic metadata that can be determined
    without parsing microagent content. Use the separate content API
    to get detailed microagent information.
    """

    name: str  # File name without extension
    git_provider: ProviderType
    path: str  # Path to the microagent in the Git provider (e.g., ".openhands/microagents/tell-me-a-joke.md")
    created_at: datetime


class MicroagentContentResponse(BaseModel):
    """Response model for individual microagent content endpoint."""

    content: str
    path: str
    git_provider: ProviderType


def _determine_microagents_path(
    repository_name: str, git_provider: ProviderType
) -> str:
    """Determine the microagents directory path based on git provider and repository name.

    Args:
        repository_name: Repository name in format 'owner/repo' or 'domain/owner/repo'
        git_provider: Git provider type

    Returns:
        The relative path to the microagents directory
    """
    actual_repo_name = _extract_repo_name(repository_name)

    if git_provider != ProviderType.GITLAB and actual_repo_name == '.openhands':
        # For non-GitLab providers with repository name ".openhands", scan "microagents" folder
        return 'microagents'
    elif git_provider == ProviderType.GITLAB and actual_repo_name == 'openhands-config':
        # For GitLab with repository name "openhands-config", scan "microagents" folder
        return 'microagents'
    else:
        # Default behavior: look for .openhands/microagents directory
        return '.openhands/microagents'


def _get_github_headers(github_token: str | None) -> dict[str, str]:
    """Get headers for GitHub API requests."""
    headers = {'Accept': 'application/vnd.github+json'}
    if github_token:
        headers['Authorization'] = f'Bearer {github_token}'
        headers['X-GitHub-Api-Version'] = '2022-11-28'
    return headers


def _get_gitlab_headers(gitlab_token: str | None) -> dict[str, str]:
    """Get headers for GitLab API requests."""
    headers = {}
    if gitlab_token:
        headers['Authorization'] = f'Bearer {gitlab_token}'
    return headers


def _get_bitbucket_headers(bitbucket_token: str | None) -> dict[str, str]:
    """Get headers for Bitbucket API requests."""
    headers = {}
    if bitbucket_token:
        headers['Authorization'] = f'Bearer {bitbucket_token}'
    return headers


def _create_microagent_response(
    file_name: str,
    git_provider: ProviderType,
    path: str,
) -> MicroagentResponse:
    """Create a MicroagentResponse from basic file information.

    Note: Content parsing is excluded from the listing API for performance optimization.
    Use the separate content API to fetch and parse individual microagent content.
    """
    # Extract name without extension
    name = file_name.replace('.md', '').replace('.cursorrules', 'cursorrules')

    return MicroagentResponse(
        name=name,
        git_provider=git_provider,
        path=path,
        created_at=datetime.now(),  # Fallback to current time
    )


async def _process_cursorrules_file(
    client: httpx.AsyncClient,
    cursorrules_url: str,
    headers: dict[str, str],
    microagents_path: str,
    git_provider: ProviderType,
    decode_base64: bool = False,
) -> MicroagentResponse | None:
    """Check if .cursorrules file exists and return basic metadata."""
    try:
        # Just check if the file exists with a HEAD request (or GET with minimal processing)
        cursorrules_response = await client.get(cursorrules_url, headers=headers)
        if cursorrules_response.status_code == 200:
            # File exists, return basic metadata without parsing content
            return _create_microagent_response(
                '.cursorrules', git_provider, '.cursorrules'
            )
    except Exception as e:
        logger.warning(f'Error checking .cursorrules: {str(e)}')
    return None


async def _process_github_md_files(
    client: httpx.AsyncClient,
    directory_contents: list,
    headers: dict[str, str],
    microagents_path: str,
) -> list[MicroagentResponse]:
    """Process .md files from GitHub directory contents without fetching content."""
    microagents = []

    for item in directory_contents:
        if (
            item['type'] == 'file'
            and item['name'].endswith('.md')
            and item['name'] != 'README.md'
        ):
            try:
                # Just create response from file metadata without fetching content
                microagents.append(
                    _create_microagent_response(
                        item['name'],
                        ProviderType.GITHUB,
                        f'{microagents_path}/{item["name"]}',
                    )
                )
            except Exception as e:
                logger.warning(f'Error processing microagent {item["name"]}: {str(e)}')

    return microagents


async def _process_gitlab_md_files(
    client: httpx.AsyncClient,
    tree_items: list,
    base_url: str,
    headers: dict[str, str],
    microagents_path: str,
) -> list[MicroagentResponse]:
    """Process .md files from GitLab tree items without fetching content."""
    microagents = []

    for item in tree_items:
        if (
            item['type'] == 'blob'
            and item['name'].endswith('.md')
            and item['name'] != 'README.md'
        ):
            try:
                # Just create response from file metadata without fetching content
                microagents.append(
                    _create_microagent_response(
                        item['name'], ProviderType.GITLAB, item['path']
                    )
                )
            except Exception as e:
                logger.warning(f'Error processing microagent {item["name"]}: {str(e)}')

    return microagents


async def _process_bitbucket_md_files(
    client: httpx.AsyncClient,
    directory_data: dict,
    repository_name: str,
    main_branch: str,
    headers: dict[str, str],
    microagents_path: str,
) -> list[MicroagentResponse]:
    """Process .md files from Bitbucket directory data without fetching content."""
    microagents = []

    if 'values' in directory_data:
        for item in directory_data['values']:
            if (
                item['type'] == 'commit_file'
                and item['path'].endswith('.md')
                and not item['path'].endswith('README.md')
            ):
                try:
                    # Extract file name from path
                    file_name = item['path'].split('/')[-1]

                    # Just create response from file metadata without fetching content
                    microagents.append(
                        _create_microagent_response(
                            file_name, ProviderType.BITBUCKET, item['path']
                        )
                    )
                except Exception as e:
                    logger.warning(
                        f'Error processing microagent {item["path"]}: {str(e)}'
                    )

    return microagents


async def _fetch_github_file_content(
    repository_name: str,
    file_path: str,
    provider_handler: ProviderHandler,
) -> str:
    """Fetch individual file content from GitHub repository.

    Args:
        repository_name: Repository name in format 'owner/repo'
        file_path: Path to the file within the repository
        provider_handler: Provider handler for authentication

    Returns:
        File content as string

    Raises:
        RuntimeError: If file cannot be fetched or doesn't exist
    """
    github_token = None
    if (
        provider_handler.provider_tokens
        and ProviderType.GITHUB in provider_handler.provider_tokens
    ):
        token = provider_handler.provider_tokens[ProviderType.GITHUB].token
        if token is not None:
            github_token = token.get_secret_value()

    headers = _get_github_headers(github_token)
    file_url = f'https://api.github.com/repos/{repository_name}/contents/{file_path}'

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(file_url, headers=headers)

            if response.status_code == 404:
                raise RuntimeError(
                    f'File not found: {file_path} in repository {repository_name}'
                )

            response.raise_for_status()
            file_data = response.json()

            # Decode base64 content
            file_content = base64.b64decode(file_data['content']).decode('utf-8')
            return file_content

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise RuntimeError(
                    f'File not found: {file_path} in repository {repository_name}'
                )
            raise RuntimeError(
                f'Failed to fetch file from GitHub: {e.response.status_code} {e.response.text}'
            )
        except Exception as e:
            raise RuntimeError(f'Error fetching file from GitHub: {str(e)}')


async def _fetch_gitlab_file_content(
    repository_name: str,
    file_path: str,
    provider_handler: ProviderHandler,
) -> str:
    """Fetch individual file content from GitLab repository.

    Args:
        repository_name: Repository name in format 'owner/repo' or 'domain/owner/repo'
        file_path: Path to the file within the repository
        provider_handler: Provider handler for authentication

    Returns:
        File content as string

    Raises:
        RuntimeError: If file cannot be fetched or doesn't exist
    """
    gitlab_token = None
    if (
        provider_handler.provider_tokens
        and ProviderType.GITLAB in provider_handler.provider_tokens
    ):
        token = provider_handler.provider_tokens[ProviderType.GITLAB].token
        if token is not None:
            gitlab_token = token.get_secret_value()

    headers = _get_gitlab_headers(gitlab_token)

    # URL encode the repository name and file path for GitLab API
    project_id = repository_name.replace('/', '%2F')
    encoded_file_path = file_path.replace('/', '%2F')

    # Determine base URL - check if it's a self-hosted GitLab instance
    if '/' in repository_name and not repository_name.startswith('gitlab.com/'):
        # Handle self-hosted GitLab (e.g., 'gitlab.example.com/owner/repo')
        parts = repository_name.split('/')
        if len(parts) >= 3:
            domain = parts[0]
            project_id = '/'.join(parts[1:]).replace('/', '%2F')
            base_url = f'https://{domain}/api/v4/projects/{project_id}'
        else:
            base_url = f'https://gitlab.com/api/v4/projects/{project_id}'
    else:
        base_url = f'https://gitlab.com/api/v4/projects/{project_id}'

    file_url = f'{base_url}/repository/files/{encoded_file_path}/raw'

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(file_url, headers=headers)

            if response.status_code == 404:
                raise RuntimeError(
                    f'File not found: {file_path} in repository {repository_name}'
                )

            response.raise_for_status()
            return response.text

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise RuntimeError(
                    f'File not found: {file_path} in repository {repository_name}'
                )
            raise RuntimeError(
                f'Failed to fetch file from GitLab: {e.response.status_code} {e.response.text}'
            )
        except Exception as e:
            raise RuntimeError(f'Error fetching file from GitLab: {str(e)}')


async def _fetch_bitbucket_file_content(
    repository_name: str,
    file_path: str,
    provider_handler: ProviderHandler,
) -> str:
    """Fetch individual file content from Bitbucket repository.

    Args:
        repository_name: Repository name in format 'workspace/repo_slug'
        file_path: Path to the file within the repository
        provider_handler: Provider handler for authentication

    Returns:
        File content as string

    Raises:
        RuntimeError: If file cannot be fetched or doesn't exist
    """
    bitbucket_token = None
    if (
        provider_handler.provider_tokens
        and ProviderType.BITBUCKET in provider_handler.provider_tokens
    ):
        token = provider_handler.provider_tokens[ProviderType.BITBUCKET].token
        if token is not None:
            bitbucket_token = token.get_secret_value()

    headers = _get_bitbucket_headers(bitbucket_token)

    async with httpx.AsyncClient() as client:
        try:
            # Step 1: Get repository info to determine the main branch
            repo_info_url = (
                f'https://api.bitbucket.org/2.0/repositories/{repository_name}'
            )
            repo_response = await client.get(repo_info_url, headers=headers)
            repo_response.raise_for_status()
            repo_data = repo_response.json()

            # Extract main branch name from repository info
            main_branch = repo_data.get('mainbranch', {}).get('name')
            if not main_branch:
                raise RuntimeError(
                    f'No main branch found in repository info for {repository_name}. '
                    f'Repository response: {repo_data.get("mainbranch", "mainbranch field missing")}'
                )

            # Step 2: Get file content using the main branch
            file_url = f'https://api.bitbucket.org/2.0/repositories/{repository_name}/src/{main_branch}/{file_path}'
            file_response = await client.get(file_url, headers=headers)

            if file_response.status_code == 404:
                raise RuntimeError(
                    f'File not found: {file_path} in repository {repository_name}'
                )

            file_response.raise_for_status()
            return file_response.text

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise RuntimeError(
                    f'File not found: {file_path} in repository {repository_name}'
                )
            raise RuntimeError(
                f'Failed to fetch file from Bitbucket: {e.response.status_code} {e.response.text}'
            )
        except Exception as e:
            raise RuntimeError(f'Error fetching file from Bitbucket: {str(e)}')


async def _fetch_file_content_via_api(
    repository_name: str,
    file_path: str,
    git_provider: ProviderType,
    provider_handler: ProviderHandler,
) -> str:
    """Fetch individual file content from repository using appropriate API.

    Args:
        repository_name: Repository name
        file_path: Path to the file within the repository
        git_provider: Git provider type
        provider_handler: Provider handler for authentication

    Returns:
        File content as string

    Raises:
        RuntimeError: If provider is unsupported or file cannot be fetched
    """
    if git_provider == ProviderType.GITHUB:
        return await _fetch_github_file_content(
            repository_name, file_path, provider_handler
        )
    elif git_provider == ProviderType.GITLAB:
        return await _fetch_gitlab_file_content(
            repository_name, file_path, provider_handler
        )
    elif git_provider == ProviderType.BITBUCKET:
        return await _fetch_bitbucket_file_content(
            repository_name, file_path, provider_handler
        )


async def _fetch_github_microagents(
    repository_name: str,
    microagents_path: str,
    provider_handler: ProviderHandler,
) -> list[MicroagentResponse]:
    """Fetch microagents from GitHub repository using GitHub Contents API.

    Args:
        repository_name: Repository name in format 'owner/repo'
        microagents_path: Path to microagents directory
        provider_handler: Provider handler for authentication

    Returns:
        List of microagents found in the repository (without content for performance)
    """
    github_token = None
    if (
        provider_handler.provider_tokens
        and ProviderType.GITHUB in provider_handler.provider_tokens
    ):
        token = provider_handler.provider_tokens[ProviderType.GITHUB].token
        if token is not None:
            github_token = token.get_secret_value()

    headers = _get_github_headers(github_token)
    base_url = f'https://api.github.com/repos/{repository_name}/contents'
    microagents = []

    async with httpx.AsyncClient() as client:
        try:
            # Use repository's default branch (no ref parameter)
            # According to GitHub API docs, this automatically uses the repository's default branch
            response = await client.get(
                f'{base_url}/{microagents_path}', headers=headers
            )

            if response.status_code == 404:
                logger.info(
                    f'No microagents directory found in {repository_name} at {microagents_path}'
                )
                return []

            response.raise_for_status()
            directory_contents = response.json()

            # Process .cursorrules if it exists
            cursorrules_response = await _process_cursorrules_file(
                client,
                f'{base_url}/.cursorrules',
                headers,
                microagents_path,
                ProviderType.GITHUB,
                decode_base64=True,
            )
            if cursorrules_response:
                microagents.append(cursorrules_response)

            # Process .md files in microagents directory
            md_microagents = await _process_github_md_files(
                client, directory_contents, headers, microagents_path
            )
            microagents.extend(md_microagents)

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.info(
                    f'No microagents directory found in {repository_name} at {microagents_path}'
                )
                return []
            raise RuntimeError(
                f'Failed to fetch microagents from GitHub: {e.response.status_code} {e.response.text}'
            )
        except Exception as e:
            raise RuntimeError(f'Error fetching microagents from GitHub: {str(e)}')

    return microagents


async def _fetch_gitlab_microagents(
    repository_name: str,
    microagents_path: str,
    provider_handler: ProviderHandler,
) -> list[MicroagentResponse]:
    """Fetch microagents from GitLab repository using GitLab API.

    Args:
        repository_name: Repository name in format 'owner/repo' or 'domain/owner/repo'
        microagents_path: Path to microagents directory
        provider_handler: Provider handler for authentication

    Returns:
        List of microagents found in the repository (without content for performance)
    """
    gitlab_token = None
    if (
        provider_handler.provider_tokens
        and ProviderType.GITLAB in provider_handler.provider_tokens
    ):
        token = provider_handler.provider_tokens[ProviderType.GITLAB].token
        if token is not None:
            gitlab_token = token.get_secret_value()

    headers = _get_gitlab_headers(gitlab_token)

    # URL encode the repository name for GitLab API
    project_id = repository_name.replace('/', '%2F')

    # Determine base URL - check if it's a self-hosted GitLab instance
    if '/' in repository_name and not repository_name.startswith('gitlab.com/'):
        # Handle self-hosted GitLab (e.g., 'gitlab.example.com/owner/repo')
        parts = repository_name.split('/')
        if len(parts) >= 3:
            domain = parts[0]
            project_id = '/'.join(parts[1:]).replace('/', '%2F')
            base_url = f'https://{domain}/api/v4/projects/{project_id}'
        else:
            base_url = f'https://gitlab.com/api/v4/projects/{project_id}'
    else:
        base_url = f'https://gitlab.com/api/v4/projects/{project_id}'

    microagents = []

    async with httpx.AsyncClient() as client:
        try:
            # Use repository's default branch (no ref parameter)
            # According to GitLab API docs, this automatically uses the repository's default branch
            tree_response = await client.get(
                f'{base_url}/repository/tree',
                headers=headers,
                params={'path': microagents_path, 'recursive': 'true'},
            )

            if tree_response.status_code == 404:
                logger.info(
                    f'No microagents directory found in {repository_name} at {microagents_path}'
                )
                return []

            tree_response.raise_for_status()
            tree_items = tree_response.json()

            # Process .cursorrules if it exists
            cursorrules_response = await _process_cursorrules_file(
                client,
                f'{base_url}/repository/files/.cursorrules/raw',
                headers,
                microagents_path,
                ProviderType.GITLAB,
                decode_base64=False,
            )
            if cursorrules_response:
                microagents.append(cursorrules_response)

            # Process .md files
            md_microagents = await _process_gitlab_md_files(
                client, tree_items, base_url, headers, microagents_path
            )
            microagents.extend(md_microagents)

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.info(
                    f'No microagents directory found in {repository_name} at {microagents_path}'
                )
                return []
            raise RuntimeError(
                f'Failed to fetch microagents from GitLab: {e.response.status_code} {e.response.text}'
            )
        except Exception as e:
            raise RuntimeError(f'Error fetching microagents from GitLab: {str(e)}')

    return microagents


async def _fetch_bitbucket_microagents(
    repository_name: str,
    microagents_path: str,
    provider_handler: ProviderHandler,
) -> list[MicroagentResponse]:
    """Fetch microagents from Bitbucket repository using Bitbucket API.

    Args:
        repository_name: Repository name in format 'workspace/repo_slug'
        microagents_path: Path to microagents directory
        provider_handler: Provider handler for authentication

    Returns:
        List of microagents found in the repository (without content for performance)
    """
    bitbucket_token = None
    if (
        provider_handler.provider_tokens
        and ProviderType.BITBUCKET in provider_handler.provider_tokens
    ):
        token = provider_handler.provider_tokens[ProviderType.BITBUCKET].token
        if token is not None:
            bitbucket_token = token.get_secret_value()

    headers = _get_bitbucket_headers(bitbucket_token)
    microagents = []

    async with httpx.AsyncClient() as client:
        try:
            # Step 1: Get repository info to determine the main branch
            repo_info_url = (
                f'https://api.bitbucket.org/2.0/repositories/{repository_name}'
            )
            repo_response = await client.get(repo_info_url, headers=headers)
            repo_response.raise_for_status()
            repo_data = repo_response.json()

            # Extract main branch name from repository info
            main_branch = repo_data.get('mainbranch', {}).get('name')
            if not main_branch:
                raise RuntimeError(
                    f'No main branch found in repository info for {repository_name}. '
                    f'Repository response: {repo_data.get("mainbranch", "mainbranch field missing")}'
                )

            # Step 2: Get microagents directory listing using the main branch
            src_url = f'https://api.bitbucket.org/2.0/repositories/{repository_name}/src/{main_branch}/{microagents_path}'
            directory_response = await client.get(src_url, headers=headers)

            if directory_response.status_code == 404:
                logger.info(
                    f'No microagents directory found in {repository_name} at {microagents_path}'
                )
                return []

            directory_response.raise_for_status()
            directory_data = directory_response.json()

            # Process .cursorrules if it exists
            cursorrules_response = await _process_cursorrules_file(
                client,
                f'https://api.bitbucket.org/2.0/repositories/{repository_name}/src/{main_branch}/.cursorrules',
                headers,
                microagents_path,
                ProviderType.BITBUCKET,
                decode_base64=False,
            )
            if cursorrules_response:
                microagents.append(cursorrules_response)

            # Process .md files in the directory
            md_microagents = await _process_bitbucket_md_files(
                client,
                directory_data,
                repository_name,
                main_branch,
                headers,
                microagents_path,
            )
            microagents.extend(md_microagents)

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.info(
                    f'No microagents directory found in {repository_name} at {microagents_path}'
                )
                return []
            raise RuntimeError(
                f'Failed to fetch microagents from Bitbucket: {e.response.status_code} {e.response.text}'
            )
        except Exception as e:
            raise RuntimeError(f'Error fetching microagents from Bitbucket: {str(e)}')

    return microagents


async def _fetch_microagents_via_api(
    repository_name: str,
    git_provider: ProviderType,
    provider_handler: ProviderHandler,
) -> list[MicroagentResponse]:
    """Fetch microagents from repository using API calls instead of cloning.

    Args:
        repository_name: Repository name
        git_provider: Git provider type
        provider_handler: Provider handler for authentication

    Returns:
        List of microagents found in the repository (without content for performance)
    """
    microagents_path = _determine_microagents_path(repository_name, git_provider)

    if git_provider == ProviderType.GITHUB:
        return await _fetch_github_microagents(
            repository_name, microagents_path, provider_handler
        )
    elif git_provider == ProviderType.GITLAB:
        return await _fetch_gitlab_microagents(
            repository_name, microagents_path, provider_handler
        )
    elif git_provider == ProviderType.BITBUCKET:
        return await _fetch_bitbucket_microagents(
            repository_name, microagents_path, provider_handler
        )


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


def _extract_repo_name(repository_name: str) -> str:
    """Extract the actual repository name from the full repository path.

    Args:
        repository_name: Repository name in format 'owner/repo' or 'domain/owner/repo'

    Returns:
        The actual repository name (last part after the last '/')
    """
    return repository_name.split('/')[-1]


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

    Note: This API returns microagent metadata without content for performance.
    Use the separate content API to fetch individual microagent content.

    Args:
        repository_name: Repository name in the format 'owner/repo' or 'domain/owner/repo'
        provider_tokens: Provider tokens for authentication
        access_token: Access token for external authentication
        user_id: User ID for authentication

    Returns:
        List of microagents found in the repository's microagents directory (without content)
    """
    try:
        # Verify repository access and get provider information
        repository = await _verify_repository_access(
            repository_name, provider_tokens, access_token, user_id
        )

        # Create provider handler for API authentication
        provider_handler = ProviderHandler(
            provider_tokens=provider_tokens
            or cast(PROVIDER_TOKEN_TYPE, MappingProxyType({})),
            external_auth_token=access_token,
            external_auth_id=user_id,
        )

        # Fetch microagents using API calls instead of cloning
        microagents = await _fetch_microagents_via_api(
            repository_name, repository.git_provider, provider_handler
        )

        logger.info(f'Found {len(microagents)} microagents in {repository_name}')
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


@app.get(
    '/repository/{repository_name:path}/microagents/content',
    response_model=MicroagentContentResponse,
)
async def get_repository_microagent_content(
    repository_name: str,
    file_path: str = Query(
        ..., description='Path to the microagent file within the repository'
    ),
    provider_tokens: PROVIDER_TOKEN_TYPE | None = Depends(get_provider_tokens),
    access_token: SecretStr | None = Depends(get_access_token),
    user_id: str | None = Depends(get_user_id),
) -> MicroagentContentResponse | JSONResponse:
    """Fetch the content of a specific microagent file from a repository.

    Args:
        repository_name: Repository name in the format 'owner/repo' or 'domain/owner/repo'
        file_path: Query parameter - Path to the microagent file within the repository
        provider_tokens: Provider tokens for authentication
        access_token: Access token for external authentication
        user_id: User ID for authentication

    Returns:
        Microagent file content and metadata

    Example:
        GET /api/user/repository/owner/repo/microagents/content?file_path=.openhands/microagents/my-agent.md
    """
    try:
        # Verify repository access and get provider information
        repository = await _verify_repository_access(
            repository_name, provider_tokens, access_token, user_id
        )

        # Create provider handler for API authentication
        provider_handler = ProviderHandler(
            provider_tokens=provider_tokens
            or cast(PROVIDER_TOKEN_TYPE, MappingProxyType({})),
            external_auth_token=access_token,
            external_auth_id=user_id,
        )

        # Fetch file content using appropriate API
        file_content = await _fetch_file_content_via_api(
            repository_name, file_path, repository.git_provider, provider_handler
        )

        logger.info(
            f'Retrieved content for microagent {file_path} from {repository_name}'
        )

        return MicroagentContentResponse(
            content=file_content,
            path=file_path,
            git_provider=repository.git_provider,
        )

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
            f'Error fetching microagent content from {repository_name}/{file_path}: {str(e)}',
            exc_info=True,
        )
        return JSONResponse(
            content=f'Error fetching microagent content: {str(e)}',
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
