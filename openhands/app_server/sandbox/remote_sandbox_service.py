from abc import ABC
import logging
import os
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Union

import base62
import httpx
from fastapi import Depends
from pydantic import Field
from sqlalchemy import Column, String, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from openhands.agent_server.utils import utc_now
from openhands.app_server.errors import SandboxError
from openhands.app_server.sandbox.sandbox_models import (
    AGENT_SERVER,
    ExposedUrl,
    SandboxInfo,
    SandboxPage,
    SandboxStatus,
)
from openhands.app_server.sandbox.sandbox_service import (
    SandboxService,
    SandboxServiceInjector,
)
from openhands.app_server.sandbox.sandbox_spec_models import SandboxSpecInfo
from openhands.app_server.sandbox.sandbox_spec_service import SandboxSpecService
from openhands.app_server.user.user_context import UserContext
from openhands.app_server.utils.sql_utils import Base, UtcDateTime

_logger = logging.getLogger(__name__)
WEBHOOK_CALLBACK_VARIABLE = 'OH_WEBHOOKS_0_BASE_URL'


class StoredRemoteSandbox(Base):  # type: ignore
    """Local storage for remote sandbox info.

    The remote runtime API does not return some variables we need, and does not
    return stopped runtimes in list operations, so we need a local copy. We use
    the remote api as a source of truth on what is currently running, not was
    run historicallly."""

    __tablename__ = 'v1_remote_sandbox'
    id = Column(String, primary_key=True)
    created_by_user_id = Column(String, nullable=True, index=True)
    sandbox_spec_id = Column(String, index=True)  # shadows runtime['image']
    created_at = Column(UtcDateTime, server_default=func.now(), index=True)


@dataclass
class RemoteSandboxService(SandboxService, ABC):
    """Sandbox service that uses HTTP to communicate with a remote runtime API.

    This service adapts the legacy RemoteRuntime HTTP protocol to work with
    the new Sandbox interface.
    """

    sandbox_spec_service: SandboxSpecService
    api_url: str
    api_key: str
    resource_factor: int
    runtime_class: str | None
    user_context: UserContext
    httpx_client: httpx.AsyncClient
    db_session: AsyncSession

    def _runtime_status_to_sandbox_status(self, runtime_status: str) -> SandboxStatus:
        """Convert runtime status to SandboxStatus."""
        status_mapping = {
            'running': SandboxStatus.RUNNING,
            'paused': SandboxStatus.PAUSED,
            'stopped': SandboxStatus.MISSING,
            'starting': SandboxStatus.STARTING,
            'error': SandboxStatus.ERROR,
        }
        return status_mapping.get(runtime_status.lower(), SandboxStatus.ERROR)

    async def _send_runtime_api_request(
        self, method: str, path: str, **kwargs: Any
    ) -> httpx.Response:
        """Send a request to the remote runtime API."""
        try:
            url = self.api_url + path
            return await self.httpx_client.request(method, url, **kwargs)
        except httpx.TimeoutException:
            _logger.error(f'No response received within timeout for URL: {url}')
            raise
        except httpx.HTTPError as e:
            _logger.error(f'HTTP error for URL {url}: {e}')
            raise

    def _to_sandbox_info(
        self, runtime: dict[str, Any] | None, stored: StoredRemoteSandbox
    ) -> SandboxInfo:
        if runtime:
            session_api_key = runtime['session_api_key']
            status = self._runtime_status_to_sandbox_status(
                runtime.get('status', 'error')
            )
            session_api_key = runtime['session_api_key']
            if status == SandboxStatus.RUNNING:
                exposed_urls = [ExposedUrl(name=AGENT_SERVER, url=runtime['url'])]
            else:
                exposed_urls = None
        else:
            session_api_key = None
            status = SandboxStatus.MISSING
            exposed_urls = None

        return SandboxInfo(
            id=stored.id,
            created_by_user_id=stored.created_by_user_id,
            sandbox_spec_id=stored.sandbox_spec_id,
            status=status,
            session_api_key=session_api_key,
            exposed_urls=exposed_urls,
            created_at=stored.created_at,
        )

    async def _secure_select(self):
        query = select(StoredRemoteSandbox)
        user_id = await self.user_context.get_user_id()
        if user_id:
            query = query.where(StoredRemoteSandbox.created_by_user_id == user_id)
        return query

    async def _init_environment(
        self, sandbox_spec: SandboxSpecInfo, sandbox_id: str
    ) -> dict[str, str]:
        environment = sandbox_spec.initial_env.copy()
        return environment

    async def search_sandboxes(
        self,
        page_id: str | None = None,
        limit: int = 100,
    ) -> SandboxPage:
        stmt = await self._secure_select()

        # Handle pagination
        if page_id is not None:
            # Parse page_id to get offset or cursor
            try:
                offset = int(page_id)
                stmt = stmt.offset(offset)
            except ValueError:
                # If page_id is not a valid integer, start from beginning
                offset = 0
        else:
            offset = 0

        # Apply limit and get one extra to check if there are more results
        stmt = stmt.limit(limit + 1).order_by(StoredRemoteSandbox.created_at.desc())

        result = await self.db_session.execute(stmt)
        stored_sandboxes = result.scalars().all()

        # Check if there are more results
        has_more = len(stored_sandboxes) > limit
        if has_more:
            stored_sandboxes = stored_sandboxes[:limit]

        # Calculate next page ID
        next_page_id = None
        if has_more:
            next_page_id = str(offset + limit)

        # Do a list to get running sandboxes
        response = await self._send_runtime_api_request('GET', '/list')
        response.raise_for_status()
        runtimes_by_session_id = {
            runtime['session_id']: runtime for runtime in response.json()['runtimes']
        }

        # Convert stored callbacks to domain models
        items = [
            self._to_sandbox_info(runtimes_by_session_id.get(s.id), s)
            for s in stored_sandboxes
        ]
        return SandboxPage(items=items, next_page_id=next_page_id)

    async def get_sandbox(self, sandbox_id: str) -> Union[SandboxInfo, None]:
        """Get a single sandbox by checking its corresponding runtime."""
        stmt = await self._secure_select()
        stmt = stmt.where(StoredRemoteSandbox.id == sandbox_id)
        result = await self.db_session.execute(stmt)
        stored_sandbox = result.scalar_one_or_none()
        if stored_sandbox is None:
            return None

        try:
            response = await self._send_runtime_api_request(
                'GET',
                '/sessions/{sandbox_id}',
            )
            response.raise_for_status()
            runtime_data = response.json()
        except Exception:
            _logger.exception('Error getting runtime: {sandbox_id}', stack_info=True)
            runtime_data = None

        return self._to_sandbox_info(runtime_data, stored_sandbox)

    async def start_sandbox(self, sandbox_spec_id: str | None = None) -> SandboxInfo:
        """Start a new sandbox by creating a remote runtime."""
        try:
            # Get sandbox spec
            if sandbox_spec_id is None:
                sandbox_spec = (
                    await self.sandbox_spec_service.get_default_sandbox_spec()
                )
            else:
                sandbox_spec_maybe = await self.sandbox_spec_service.get_sandbox_spec(
                    sandbox_spec_id
                )
                if sandbox_spec_maybe is None:
                    raise ValueError('Sandbox Spec not found')
                sandbox_spec = sandbox_spec_maybe

            # Create a unique id
            sandbox_id = base62.encodebytes(os.urandom(16))

            # get user id
            user_id = self.user_context.get_user_id()

            # Store the sandbox
            stored_sandbox = StoredRemoteSandbox(
                id=sandbox_id,
                created_by_user_id=user_id,
                sandbox_spec_id=sandbox_spec_id,
                created_at=utc_now(),
            )
            self.db_session.add(stored_sandbox)
            await self.db_session.commit()

            # Prepare environment variables
            environment = self._init_environment(sandbox_spec, sandbox_id)

            # Prepare start request
            start_request: dict[str, Any] = {
                'image': sandbox_spec.id,  # Use sandbox_spec.id as the container image
                'command': sandbox_spec.command,
                'working_dir': sandbox_spec.working_dir,
                'environment': environment,
                'session_id': sandbox_id,  # Use sandbox_id as session_id
                'resource_factor': self.resource_factor,
            }

            # Add runtime class if specified
            if self.runtime_class == 'sysbox':
                start_request['runtime_class'] = 'sysbox-runc'

            # Start the runtime
            response = await self._send_runtime_api_request(
                'POST',
                '/start',
                json=start_request,
            )
            response.raise_for_status()
            runtime_data = response.json()

            return self._to_sandbox_info(runtime_data, stored_sandbox)

        except httpx.HTTPError as e:
            _logger.error(f'Failed to start sandbox: {e}')
            raise SandboxError(f'Failed to start sandbox: {e}')

    async def resume_sandbox(self, sandbox_id: str) -> bool:
        """Resume a paused sandbox."""
        try:
            response = await self._send_runtime_api_request(
                'POST',
                '/resume',
                json={'runtime_id': sandbox_id},
            )

            if response.status_code == 404:
                return False

            response.raise_for_status()
            return True

        except httpx.HTTPError as e:
            _logger.error(f'Error resuming sandbox {sandbox_id}: {e}')
            return False

    async def pause_sandbox(self, sandbox_id: str) -> bool:
        """Pause a running sandbox."""
        try:
            response = await self._send_runtime_api_request(
                'POST',
                '/pause',
                json={'runtime_id': sandbox_id},
            )

            if response.status_code == 404:
                return False

            response.raise_for_status()
            return True

        except httpx.HTTPError as e:
            _logger.error(f'Error pausing sandbox {sandbox_id}: {e}')
            return False

    async def delete_sandbox(self, sandbox_id: str) -> bool:
        """Delete a sandbox by stopping its runtime."""
        try:
            response = await self._send_runtime_api_request(
                'POST',
                '/stop',
                json={'runtime_id': sandbox_id},
            )

            if response.status_code == 404:
                return False

            response.raise_for_status()
            return True

        except httpx.HTTPError as e:
            _logger.error(f'Error deleting sandbox {sandbox_id}: {e}')
            return False


@dataclass
class CallbackRemoteSandboxService(RemoteSandboxService):
    """ RemoteSandboxService which uses callbacks to keep conversations
    and events stored on the app server in sync with the agent servers.

    Typically used in hosted deployments where the app server has a public
    facling url"""
    web_url: str

    async def _init_environment(
        self, sandbox_spec: SandboxSpecInfo, sandbox_id: str
    ) -> dict[str, str]:
        environment = sandbox_spec.initial_env.copy()
        environment[WEBHOOK_CALLBACK_VARIABLE] = (
            f'{self.web_url}/api/v1/webhooks/{sandbox_id}'
        )
        return environment


class RemoteSandboxServiceInjector(SandboxServiceInjector):
    """Dependency injector for remote sandbox services."""

    api_url: str = Field(description='The API URL for remote runtimes')
    api_key: str = Field(description='The API Key for remote runtimes')
    resource_factor: int = Field(
        default=1,
        description='Factor by which to scale resources in sandbox: 1, 2, 4, or 8',
    )
    runtime_class: str = Field(
        default='sysbox',
        description='# can be "None" (default to gvisor) or "sysbox" (support docker inside runtime + more stable)',
    )

    def get_injector(self) -> Callable[..., Awaitable[SandboxService]]:
        # Define inline to prevent circular lookup
        from openhands.app_server.config import (
            db_service,
            get_global_config,
            httpx_client_injector,
            sandbox_spec_injector,
            user_injector,
        )

        config = get_global_config()
        web_url = config.web_url
        if web_url is None:
            # TODO: Develop a polling protocol so this is not required.
            raise SandboxError('A web_url is required in order to use RemoteSandboxes!')
        # Create dependencies at module level to avoid B008
        _sandbox_spec_dependency = Depends(sandbox_spec_injector())
        user_dependency = Depends(user_injector())
        _httpx_client_dependency = Depends(httpx_client_injector())
        db_session_dependency = Depends(db_service().managed_session_dependency)

        async def resolve_sandbox_service(
            sandbox_spec_service: SandboxSpecService = _sandbox_spec_dependency,
            user_context: UserContext = user_dependency,
            httpx_client: httpx.AsyncClient = _httpx_client_dependency,
            db_session: AsyncSession = db_session_dependency,
        ) -> SandboxService:
            return CallbackRemoteSandboxService(
                sandbox_spec_service=sandbox_spec_service,
                api_url=self.api_url,
                api_key=self.api_key,
                web_url=web_url,
                resource_factor=self.resource_factor,
                runtime_class=self.runtime_class,
                user_context=user_context,
                httpx_client=httpx_client,
                db_session=db_session,
            )

        return resolve_sandbox_service
