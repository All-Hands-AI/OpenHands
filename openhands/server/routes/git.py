from types import MappingProxyType
from typing import Any, cast

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import JSONResponse
from pydantic import SecretStr

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
from openhands.microagent.types import (
    MicroagentContentResponse,
    MicroagentResponse,
)
from openhands.server.dependencies import get_dependencies
from openhands.server.shared import server_config
from openhands.server.user_auth import (
    get_access_token,
    get_provider_tokens,
    get_user_id,
    get_user_info,
)

app = APIRouter(prefix='/api/user', dependencies=get_dependencies())


@app.get('/repositories', response_model=list[Repository])
async def get_user_repositories(
    sort: str = 'pushed',
    provider_tokens: PROVIDER_TOKEN_TYPE | None = Depends(get_provider_tokens),
    access_token: SecretStr | None = Depends(get_access_token),
    user_id: str | None = Depends(get_user_id),
    user_info: dict | None = Depends(get_user_info),
) -> list[Repository] | JSONResponse:
    retval = _check_idp_type(
        user_info=user_info, default_value=cast(list[Repository], [])
    )
    if retval is not None:
        return retval

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
    user_info: dict | None = Depends(get_user_info),
) -> User | JSONResponse:
    retval = _check_idp_type(
        user_info=user_info,
        default_value=User(
            id=(user_info.get('sub') if user_info else '') or '',
            login=(user_info.get('preferred_username') if user_info else '') or '',
            avatar_url='',
            email=user_info.get('email') if user_info else None,
        ),
    )
    if retval is not None:
        return retval

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
    user_info: dict | None = Depends(get_user_info),
) -> list[Repository] | JSONResponse:
    retval = _check_idp_type(
        user_info=user_info, default_value=cast(list[Repository], [])
    )
    if retval is not None:
        return retval

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
    user_info: dict | None = Depends(get_user_info),
) -> list[SuggestedTask] | JSONResponse:
    """Get suggested tasks for the authenticated user across their most recently pushed repositories.

    Returns:
    - PRs owned by the user
    - Issues assigned to the user.
    """
    retval = _check_idp_type(
        user_info=user_info, default_value=cast(list[SuggestedTask], [])
    )
    if retval is not None:
        return retval

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
    user_info: dict | None = Depends(get_user_info),
) -> list[Branch] | JSONResponse:
    """Get branches for a repository.

    Args:
        repository: The repository name in the format 'owner/repo'

    Returns:
        A list of branches for the repository
    """
    retval = _check_idp_type(user_info=user_info, default_value=cast(list[Branch], []))
    if retval is not None:
        return retval

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
        # Create provider handler for API authentication
        provider_handler = ProviderHandler(
            provider_tokens=provider_tokens
            or cast(PROVIDER_TOKEN_TYPE, MappingProxyType({})),
            external_auth_token=access_token,
            external_auth_id=user_id,
        )

        # Fetch microagents using the provider handler
        microagents = await provider_handler.get_microagents(repository_name)

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
        # Create provider handler for API authentication
        provider_handler = ProviderHandler(
            provider_tokens=provider_tokens
            or cast(PROVIDER_TOKEN_TYPE, MappingProxyType({})),
            external_auth_token=access_token,
            external_auth_id=user_id,
        )

        # Fetch file content using the provider handler
        response = await provider_handler.get_microagent_content(
            repository_name, file_path
        )

        logger.info(
            f'Retrieved content for microagent {file_path} from {repository_name}'
        )

        return response

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


def _check_idp_type(user_info: dict | None, default_value: Any):
    if not user_info:
        return JSONResponse(
            content='No user_info found for user.',
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
    idp = user_info.get('identity_provider')
    if not idp:
        return JSONResponse(
            content='IDP not found.',
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
    # Enterprise SSO provider has no provider tokens
    if ProviderType(idp) == ProviderType.ENTERPRISE_SSO:
        return JSONResponse(
            content={},
            status_code=status.HTTP_200_OK,
        )

    return None
