import asyncio

from integrations.gitlab.gitlab_service import SaaSGitLabService
from pydantic import SecretStr

from openhands.core.logger import openhands_logger as logger
from openhands.server.types import AppMode


def schedule_gitlab_repo_sync(
    user_id: str, keycloak_access_token: SecretStr | None = None
) -> None:
    """Schedule a background sync of GitLab repositories and webhook tracking.

    Because the outer call is already a background task, we instruct the service
    to store repository data synchronously (store_in_background=False) to avoid
    nested background tasks while still keeping the overall operation async.
    """

    async def _run():
        try:
            service = SaaSGitLabService(
                external_auth_id=user_id, external_auth_token=keycloak_access_token
            )
            await service.get_all_repositories(
                'pushed', AppMode.SAAS, store_in_background=False
            )
        except Exception:
            logger.warning('gitlab_repo_sync_failed', exc_info=True)

    asyncio.create_task(_run())
