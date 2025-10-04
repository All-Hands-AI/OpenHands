from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from openhands.app_server.sandbox.remote_sandbox_service import (
    RemoteSandboxConfig,
    RemoteSandboxService,
)
from openhands.app_server.sandbox.sandbox_models import SandboxStatus
from openhands.app_server.sandbox.sandbox_spec_models import SandboxSpecInfo
from openhands.app_server.sandbox.sandbox_spec_service import SandboxSpecService


@pytest.fixture
def mock_sandbox_spec_service():
    """Mock sandbox spec service."""
    service = MagicMock(spec=SandboxSpecService)

    # Mock default sandbox spec
    default_spec = SandboxSpecInfo(
        id='test-image:latest',
        command='python -m openhands.runtime.action_execution.action_execution_server',
        created_at=datetime.now(),
        initial_env={'TEST_VAR': 'test_value'},
        working_dir='/openhands/code/',
    )
    service.get_default_sandbox_spec = AsyncMock(return_value=default_spec)
    service.get_sandbox_spec = AsyncMock(return_value=default_spec)

    return service


@pytest.fixture
def mock_httpx_client():
    """Mock httpx client."""
    client = MagicMock(spec=httpx.AsyncClient)
    client.headers = {}
    return client


@pytest.fixture
def remote_sandbox_config():
    """Remote sandbox configuration."""
    return RemoteSandboxConfig(
        remote_runtime_api_url='http://test-api.example.com',
        api_key='test-api-key',
        container_url_pattern='http://localhost:{port}',
    )


@pytest.fixture
def remote_sandbox_service(
    mock_sandbox_spec_service, mock_httpx_client, remote_sandbox_config
):
    """Remote sandbox service instance."""
    service = RemoteSandboxService(
        sandbox_spec_service=mock_sandbox_spec_service,
        config=remote_sandbox_config,
        httpx_client=mock_httpx_client,
    )
    return service


class TestRemoteSandboxService:
    """Test cases for RemoteSandboxService."""

    def test_init_sets_auth_headers(self, remote_sandbox_service, mock_httpx_client):
        """Test that initialization sets authentication headers."""
        assert mock_httpx_client.headers['X-API-Key'] == 'test-api-key'
        assert hasattr(mock_httpx_client, '_auth_configured')

    def test_runtime_status_mapping(self, remote_sandbox_service):
        """Test runtime status to sandbox status mapping."""
        assert (
            remote_sandbox_service._runtime_status_to_sandbox_status('running')
            == SandboxStatus.RUNNING
        )
        assert (
            remote_sandbox_service._runtime_status_to_sandbox_status('paused')
            == SandboxStatus.PAUSED
        )
        assert (
            remote_sandbox_service._runtime_status_to_sandbox_status('stopped')
            == SandboxStatus.MISSING
        )
        assert (
            remote_sandbox_service._runtime_status_to_sandbox_status('starting')
            == SandboxStatus.STARTING
        )
        assert (
            remote_sandbox_service._runtime_status_to_sandbox_status('error')
            == SandboxStatus.ERROR
        )
        assert (
            remote_sandbox_service._runtime_status_to_sandbox_status('unknown')
            == SandboxStatus.ERROR
        )

    def test_generate_sandbox_id(self, remote_sandbox_service):
        """Test sandbox ID generation."""
        sandbox_id = remote_sandbox_service._generate_sandbox_id()
        assert sandbox_id.startswith('sandbox-')
        assert len(sandbox_id) > len('sandbox-')
        # Should be URL-safe base64 without padding
        encoded_part = sandbox_id[8:]  # Remove 'sandbox-' prefix
        assert '=' not in encoded_part  # No padding
        assert '+' not in encoded_part  # URL-safe
        assert '/' not in encoded_part  # URL-safe

    def test_generate_session_api_key(self, remote_sandbox_service):
        """Test session API key generation."""
        api_key = remote_sandbox_service._generate_session_api_key()
        assert isinstance(api_key, str)
        assert len(api_key) > 0

    @pytest.mark.asyncio
    async def test_send_runtime_api_request_success(
        self, remote_sandbox_service, mock_httpx_client
    ):
        """Test successful API request."""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'status': 'success'}
        mock_httpx_client.request = AsyncMock(return_value=mock_response)

        response = await remote_sandbox_service._send_runtime_api_request(
            'GET', 'http://test.com/api'
        )

        assert response == mock_response
        mock_httpx_client.request.assert_called_once_with(
            'GET', 'http://test.com/api', timeout=300
        )

    @pytest.mark.asyncio
    async def test_send_runtime_api_request_timeout(
        self, remote_sandbox_service, mock_httpx_client
    ):
        """Test API request timeout."""
        mock_httpx_client.request = AsyncMock(
            side_effect=httpx.TimeoutException('Timeout')
        )

        with pytest.raises(httpx.TimeoutException):
            await remote_sandbox_service._send_runtime_api_request(
                'GET', 'http://test.com/api'
            )

    @pytest.mark.asyncio
    async def test_get_sandbox_not_found(
        self, remote_sandbox_service, mock_httpx_client
    ):
        """Test getting a sandbox that doesn't exist."""
        # Mock 404 response
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_httpx_client.request = AsyncMock(return_value=mock_response)

        result = await remote_sandbox_service.get_sandbox('nonexistent-sandbox')
        assert result is None

    @pytest.mark.asyncio
    async def test_get_sandbox_success(self, remote_sandbox_service, mock_httpx_client):
        """Test successfully getting a sandbox."""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'status': 'running',
            'runtime_id': 'runtime-123',
            'url': 'http://localhost:8000',
            'work_hosts': {'host1': 8001},
            'session_api_key': 'session-key-123',
            'sandbox_spec_id': 'test-spec',
        }
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.request = AsyncMock(return_value=mock_response)

        result = await remote_sandbox_service.get_sandbox('test-sandbox')

        assert result is not None
        assert result.id == 'test-sandbox'
        assert result.status == SandboxStatus.RUNNING
        assert result.session_api_key == 'session-key-123'
        assert len(result.exposed_urls) > 0

    @pytest.mark.asyncio
    async def test_start_sandbox_success(
        self, remote_sandbox_service, mock_httpx_client
    ):
        """Test successfully starting a sandbox."""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'runtime_id': 'runtime-123',
            'url': 'http://localhost:8000',
            'work_hosts': {'host1': 8001},
            'session_api_key': 'session-key-123',
        }
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.request = AsyncMock(return_value=mock_response)

        result = await remote_sandbox_service.start_sandbox('test-spec')

        assert result is not None
        assert result.status == SandboxStatus.RUNNING
        assert result.sandbox_spec_id == 'test-image:latest'
        assert result.session_api_key == 'session-key-123'
        assert len(result.exposed_urls) > 0

        # Verify the API call was made correctly
        mock_httpx_client.request.assert_called_once()
        call_args = mock_httpx_client.request.call_args
        assert call_args[0][0] == 'POST'  # method
        assert call_args[0][1].endswith('/start')  # URL
        assert 'json' in call_args[1]  # request body

    @pytest.mark.asyncio
    async def test_start_sandbox_http_error(
        self, remote_sandbox_service, mock_httpx_client
    ):
        """Test starting a sandbox with HTTP error."""
        from openhands.app_server.errors import SandboxError

        # Mock HTTP error
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.raise_for_status = MagicMock(
            side_effect=httpx.HTTPStatusError(
                'Server error', request=MagicMock(), response=mock_response
            )
        )
        mock_httpx_client.request = AsyncMock(return_value=mock_response)

        with pytest.raises(SandboxError):
            await remote_sandbox_service.start_sandbox('test-spec')

    @pytest.mark.asyncio
    async def test_resume_sandbox_success(
        self, remote_sandbox_service, mock_httpx_client
    ):
        """Test successfully resuming a sandbox."""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.request = AsyncMock(return_value=mock_response)

        result = await remote_sandbox_service.resume_sandbox('test-sandbox')
        assert result is True

        # Verify the API call
        mock_httpx_client.request.assert_called_once()
        call_args = mock_httpx_client.request.call_args
        assert call_args[0][0] == 'POST'  # method
        assert call_args[0][1].endswith('/resume')  # URL

    @pytest.mark.asyncio
    async def test_resume_sandbox_not_found(
        self, remote_sandbox_service, mock_httpx_client
    ):
        """Test resuming a sandbox that doesn't exist."""
        # Mock 404 response
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_httpx_client.request = AsyncMock(return_value=mock_response)

        result = await remote_sandbox_service.resume_sandbox('nonexistent-sandbox')
        assert result is False

    @pytest.mark.asyncio
    async def test_pause_sandbox_success(
        self, remote_sandbox_service, mock_httpx_client
    ):
        """Test successfully pausing a sandbox."""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.request = AsyncMock(return_value=mock_response)

        result = await remote_sandbox_service.pause_sandbox('test-sandbox')
        assert result is True

    @pytest.mark.asyncio
    async def test_delete_sandbox_success(
        self, remote_sandbox_service, mock_httpx_client
    ):
        """Test successfully deleting a sandbox."""
        # Set up mapping
        remote_sandbox_service._sandbox_to_runtime_mapping['test-sandbox'] = (
            'runtime-123'
        )
        remote_sandbox_service._runtime_to_sandbox_mapping['runtime-123'] = (
            'test-sandbox'
        )

        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.request = AsyncMock(return_value=mock_response)

        result = await remote_sandbox_service.delete_sandbox('test-sandbox')
        assert result is True

        # Verify mappings were cleaned up
        assert 'test-sandbox' not in remote_sandbox_service._sandbox_to_runtime_mapping
        assert 'runtime-123' not in remote_sandbox_service._runtime_to_sandbox_mapping

    @pytest.mark.asyncio
    async def test_search_sandboxes_returns_empty(self, remote_sandbox_service):
        """Test that search_sandboxes returns empty results (not implemented)."""
        result = await remote_sandbox_service.search_sandboxes()
        assert result.items == []
        assert result.next_page_id is None

    @pytest.mark.asyncio
    async def test_create_exposed_urls(self, remote_sandbox_service):
        """Test creating exposed URLs from runtime information."""
        runtime_url = 'http://localhost:8000'
        available_hosts = {'host1': 8001}

        urls = await remote_sandbox_service._create_exposed_urls(
            runtime_url, available_hosts
        )

        assert len(urls) >= 1  # At least agent server URL
        agent_server_url = next(
            (url for url in urls if url.name == 'AGENT_SERVER'), None
        )
        assert agent_server_url is not None
        assert agent_server_url.url == runtime_url

    @pytest.mark.asyncio
    async def test_parse_runtime_response(self, remote_sandbox_service):
        """Test parsing runtime response data."""
        response_data = {
            'runtime_id': 'runtime-123',
            'url': 'http://localhost:8000',
            'work_hosts': {'host1': 8001},
            'session_api_key': 'session-key-123',
        }

        (
            runtime_id,
            runtime_url,
            available_hosts,
            session_api_key,
        ) = await remote_sandbox_service._parse_runtime_response(response_data)

        assert runtime_id == 'runtime-123'
        assert runtime_url == 'http://localhost:8000'
        assert available_hosts == {'host1': 8001}
        assert session_api_key == 'session-key-123'
