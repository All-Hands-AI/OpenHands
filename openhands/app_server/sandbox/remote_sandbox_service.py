import base64
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Union
from urllib.parse import urlparse

import httpx
from fastapi import Depends
from pydantic import BaseModel, Field

from openhands.app_server.errors import SandboxError
from openhands.app_server.sandbox.sandbox_models import (
    AGENT_SERVER,
    VSCODE,
    ExposedUrl,
    SandboxInfo,
    SandboxPage,
    SandboxStatus,
)
from openhands.app_server.sandbox.sandbox_service import (
    SandboxService,
    SandboxServiceManager,
)
from openhands.app_server.sandbox.sandbox_spec_service import SandboxSpecService
from openhands.app_server.user.legacy_user_service import ROOT_USER

_logger = logging.getLogger(__name__)


class RemoteSandboxConfig(BaseModel):
    """Configuration for remote sandbox service."""

    remote_runtime_api_url: str = Field(
        description='Base URL for the remote runtime API'
    )
    api_key: str = Field(
        description='API key for authenticating with the remote runtime API'
    )
    container_url_pattern: str = Field(
        default='https://work-{port}-{host}.{domain}',
        description='URL pattern for accessing containers',
    )
    session_api_key_variable: str = Field(
        default='OH_SESSION_API_KEYS_0',
        description='Environment variable name for session API key',
    )
    webhook_callback_variable: str = Field(
        default='OH_WEBHOOKS_0_BASE_URL',
        description='Environment variable name for webhook callback URL',
    )
    health_check_path: str | None = Field(
        default='/health', description='Path to check for container health'
    )
    remote_runtime_api_timeout: int = Field(
        default=300, description='Timeout for remote runtime API requests in seconds'
    )
    remote_runtime_resource_factor: float = Field(
        default=1.0, description='Resource factor for remote runtime containers'
    )
    remote_runtime_class: str | None = Field(
        default=None, description='Runtime class (sysbox, gvisor, etc.)'
    )


@dataclass
class RemoteSandboxService(SandboxService):
    """Sandbox service that uses HTTP to communicate with a remote runtime API.

    This service adapts the legacy RemoteRuntime HTTP protocol to work with
    the new Sandbox interface.
    """

    sandbox_spec_service: SandboxSpecService
    config: RemoteSandboxConfig
    httpx_client: httpx.AsyncClient

    # Internal mapping from sandbox_id to runtime_id
    _sandbox_to_runtime_mapping: dict[str, str] = field(default_factory=dict)
    _runtime_to_sandbox_mapping: dict[str, str] = field(default_factory=dict)

    def __post_init__(self):
        """Initialize HTTP session with authentication headers."""
        # Set up authentication headers
        if not hasattr(self.httpx_client, '_auth_configured'):
            self.httpx_client.headers.update({'X-API-Key': self.config.api_key})
            self.httpx_client._auth_configured = True  # type: ignore

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

    def _generate_sandbox_id(self) -> str:
        """Generate a unique sandbox ID."""
        random_bytes = os.urandom(16)
        # Use base64 encoding and make it URL-safe
        encoded = base64.urlsafe_b64encode(random_bytes).decode('ascii').rstrip('=')
        return f'sandbox-{encoded}'

    def _generate_session_api_key(self) -> str:
        """Generate a session API key."""
        random_bytes = os.urandom(32)
        # Use base64 encoding and make it URL-safe
        return base64.urlsafe_b64encode(random_bytes).decode('ascii').rstrip('=')

    async def _send_runtime_api_request(
        self, method: str, url: str, **kwargs: Any
    ) -> httpx.Response:
        """Send a request to the remote runtime API."""
        try:
            kwargs['timeout'] = self.config.remote_runtime_api_timeout
            return await self.httpx_client.request(method, url, **kwargs)
        except httpx.TimeoutException:
            _logger.error(f'No response received within timeout for URL: {url}')
            raise
        except httpx.HTTPError as e:
            _logger.error(f'HTTP error for URL {url}: {e}')
            raise

    async def _parse_runtime_response(
        self, response_data: dict[str, Any]
    ) -> tuple[str, str, dict[str, int], str | None]:
        """Parse runtime response and extract key information.

        Returns:
            Tuple of (runtime_id, runtime_url, available_hosts, session_api_key)
        """
        runtime_id = response_data['runtime_id']
        runtime_url = response_data['url']
        available_hosts = response_data.get('work_hosts', {})
        session_api_key = response_data.get('session_api_key')

        return runtime_id, runtime_url, available_hosts, session_api_key

    async def _create_exposed_urls(
        self, runtime_url: str, available_hosts: dict[str, int]
    ) -> list[ExposedUrl]:
        """Create exposed URLs from runtime information."""
        exposed_urls = []

        # Parse the runtime URL to understand the pattern
        parsed = urlparse(runtime_url)

        # Create agent server URL
        exposed_urls.append(ExposedUrl(name=AGENT_SERVER, url=runtime_url))

        # Create VSCode URL if available
        if available_hosts:
            # Try to construct VSCode URL based on the pattern
            # This is a simplified approach - in practice, you might need more sophisticated URL construction
            scheme, netloc = parsed.scheme, parsed.netloc
            vscode_url = f'{scheme}://vscode-{netloc}/'
            exposed_urls.append(ExposedUrl(name=VSCODE, url=vscode_url))

        return exposed_urls

    async def _runtime_info_to_sandbox_info(
        self,
        sandbox_id: str,
        runtime_data: dict[str, Any],
        sandbox_spec_id: str,
        created_by_user_id: str = ROOT_USER,
        created_at: datetime | None = None,
        assume_running: bool = False,
    ) -> SandboxInfo:
        """Convert runtime information to SandboxInfo."""
        # If assume_running is True (e.g., from start_sandbox), assume it's running
        # unless explicitly stated otherwise
        if assume_running and 'status' not in runtime_data:
            status = SandboxStatus.RUNNING
        else:
            status = self._runtime_status_to_sandbox_status(
                runtime_data.get('status', 'error')
            )

        exposed_urls = None
        session_api_key = None

        if status == SandboxStatus.RUNNING:
            (
                runtime_id,
                runtime_url,
                available_hosts,
                api_key,
            ) = await self._parse_runtime_response(runtime_data)
            exposed_urls = await self._create_exposed_urls(runtime_url, available_hosts)
            session_api_key = api_key

            # Update mappings
            self._sandbox_to_runtime_mapping[sandbox_id] = runtime_id
            self._runtime_to_sandbox_mapping[runtime_id] = sandbox_id

        return SandboxInfo(
            id=sandbox_id,
            created_by_user_id=created_by_user_id,
            sandbox_spec_id=sandbox_spec_id,
            status=status,
            session_api_key=session_api_key,
            exposed_urls=exposed_urls,
            created_at=created_at or datetime.now(timezone.utc),
        )

    async def search_sandboxes(
        self,
        created_by_user_id__eq: str | None = None,
        page_id: str | None = None,
        limit: int = 100,
    ) -> SandboxPage:
        """Search for sandboxes.

        Note: The remote runtime API doesn't have a direct equivalent to search,
        so this implementation returns an empty page. In a real implementation,
        you might need to maintain a registry of active sandboxes.
        """
        # The remote runtime API doesn't have a search endpoint
        # In practice, you might need to maintain a local registry or
        # extend the remote API to support sandbox listing
        _logger.warning('search_sandboxes not fully supported with remote runtime API')
        return SandboxPage(items=[], next_page_id=None)

    async def get_sandbox(self, sandbox_id: str) -> Union[SandboxInfo, None]:
        """Get a single sandbox by checking its corresponding runtime."""
        try:
            # Check if we have a runtime mapping for this sandbox
            runtime_id = self._sandbox_to_runtime_mapping.get(sandbox_id)
            if not runtime_id:
                # Try to use sandbox_id as session_id (for compatibility)
                runtime_id = sandbox_id

            # Query the runtime API
            response = await self._send_runtime_api_request(
                'GET',
                f'{self.config.remote_runtime_api_url}/sessions/{runtime_id}',
            )

            if response.status_code == 404:
                return None

            response.raise_for_status()
            runtime_data = response.json()

            # We need to determine the sandbox_spec_id somehow
            # In practice, this might be stored in the runtime metadata
            # For now, we'll use a default
            sandbox_spec_id = runtime_data.get('sandbox_spec_id', 'default')

            return await self._runtime_info_to_sandbox_info(
                sandbox_id=sandbox_id,
                runtime_data=runtime_data,
                sandbox_spec_id=sandbox_spec_id,
            )

        except httpx.HTTPError as e:
            if e.response and e.response.status_code == 404:
                return None
            _logger.error(f'Error getting sandbox {sandbox_id}: {e}')
            return None

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

            # Generate sandbox ID and session API key
            sandbox_id = self._generate_sandbox_id()
            session_api_key = self._generate_session_api_key()

            # Prepare environment variables
            environment = sandbox_spec.initial_env.copy()
            environment[self.config.session_api_key_variable] = session_api_key

            # Add webhook callback if needed
            if self.config.webhook_callback_variable:
                # This would need to be adapted based on your webhook setup
                environment[self.config.webhook_callback_variable] = (
                    f'http://localhost:3000/api/v1/webhooks/{sandbox_id}'
                )

            # Prepare start request
            start_request: dict[str, Any] = {
                'image': sandbox_spec.id,  # Use sandbox_spec.id as the container image
                'command': [
                    'python',
                    '-m',
                    'openhands.runtime.action_execution.action_execution_server',
                ],
                'working_dir': sandbox_spec.working_dir or '/openhands/code/',
                'environment': environment,
                'session_id': sandbox_id,  # Use sandbox_id as session_id
                'resource_factor': self.config.remote_runtime_resource_factor,
            }

            # Add runtime class if specified
            if self.config.remote_runtime_class == 'sysbox':
                start_request['runtime_class'] = 'sysbox-runc'

            # Start the runtime
            response = await self._send_runtime_api_request(
                'POST',
                f'{self.config.remote_runtime_api_url}/start',
                json=start_request,
            )
            response.raise_for_status()

            runtime_data = response.json()

            return await self._runtime_info_to_sandbox_info(
                sandbox_id=sandbox_id,
                runtime_data=runtime_data,
                sandbox_spec_id=sandbox_spec.id,
                created_by_user_id=ROOT_USER,
                assume_running=True,
            )

        except httpx.HTTPError as e:
            _logger.error(f'Failed to start sandbox: {e}')
            raise SandboxError(f'Failed to start sandbox: {e}')

    async def resume_sandbox(self, sandbox_id: str) -> bool:
        """Resume a paused sandbox."""
        try:
            # Get runtime ID for this sandbox
            runtime_id = self._sandbox_to_runtime_mapping.get(sandbox_id, sandbox_id)

            response = await self._send_runtime_api_request(
                'POST',
                f'{self.config.remote_runtime_api_url}/resume',
                json={'runtime_id': runtime_id},
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
            # Get runtime ID for this sandbox
            runtime_id = self._sandbox_to_runtime_mapping.get(sandbox_id, sandbox_id)

            response = await self._send_runtime_api_request(
                'POST',
                f'{self.config.remote_runtime_api_url}/pause',
                json={'runtime_id': runtime_id},
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
            # Get runtime ID for this sandbox
            runtime_id = self._sandbox_to_runtime_mapping.get(sandbox_id, sandbox_id)

            response = await self._send_runtime_api_request(
                'POST',
                f'{self.config.remote_runtime_api_url}/stop',
                json={'runtime_id': runtime_id},
            )

            if response.status_code == 404:
                return False

            response.raise_for_status()

            # Clean up mappings
            if sandbox_id in self._sandbox_to_runtime_mapping:
                runtime_id = self._sandbox_to_runtime_mapping.pop(sandbox_id)
                self._runtime_to_sandbox_mapping.pop(runtime_id, None)

            return True

        except httpx.HTTPError as e:
            _logger.error(f'Error deleting sandbox {sandbox_id}: {e}')
            return False


class RemoteSandboxServiceManager(SandboxServiceManager):
    """Manager for remote sandbox services."""

    config: RemoteSandboxConfig = Field(
        description='Configuration for the remote sandbox service'
    )

    def get_resolver_for_current_user(self) -> Callable:
        # Remote sandboxes can be user-scoped if needed
        return self.get_unsecured_resolver()

    def get_unsecured_resolver(self) -> Callable:
        # Define inline to prevent circular lookup
        from openhands.app_server.config import (
            httpx_client_manager,
            sandbox_spec_manager,
        )

        # Create dependencies at module level to avoid B008
        _sandbox_spec_dependency = Depends(
            sandbox_spec_manager().get_unsecured_resolver()
        )
        _httpx_client_dependency = Depends(httpx_client_manager().resolve)

        def resolve_sandbox_service(
            sandbox_spec_service: SandboxSpecService = _sandbox_spec_dependency,
            httpx_client: httpx.AsyncClient = _httpx_client_dependency,
        ) -> SandboxService:
            return RemoteSandboxService(
                sandbox_spec_service=sandbox_spec_service,
                config=self.config,
                httpx_client=httpx_client,
            )

        return resolve_sandbox_service
