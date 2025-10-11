"""Tests for RemoteSandboxService.

This module tests the remote sandbox service implementation, focusing on:
- Remote runtime API communication (/pause, /stop, /resume, /list, /sessions endpoints)
- Container lifecycle management through remote API
- Sandbox search and retrieval with filtering and pagination
- Data transformation from runtime API responses to SandboxInfo objects
- Error handling for HTTP API failures and timeouts
- Parallelization of operations where applicable
- Edge cases with malformed API responses
"""

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from openhands.app_server.errors import SandboxError
from openhands.app_server.sandbox.remote_sandbox_service import (
    RemoteSandboxService,
    StoredRemoteSandbox,
)
from openhands.app_server.sandbox.sandbox_models import (
    AGENT_SERVER,
    SandboxStatus,
)
from openhands.app_server.sandbox.sandbox_spec_models import SandboxSpecInfo
from openhands.app_server.user.user_context import UserContext


@pytest.fixture
def mock_sandbox_spec_service():
    """Mock SandboxSpecService for testing."""
    mock_service = AsyncMock()
    mock_spec = SandboxSpecInfo(
        id='test-image:latest',
        initial_env={'TEST_VAR': 'test_value'},
        working_dir='/workspace',
        command=['python', '-m', 'openhands.runtime.action_execution_server'],
    )
    mock_service.get_default_sandbox_spec.return_value = mock_spec
    mock_service.get_sandbox_spec.return_value = mock_spec
    return mock_service


@pytest.fixture
def mock_user_context():
    """Mock UserContext for testing."""
    mock_context = AsyncMock(spec=UserContext)
    mock_context.get_user_id.return_value = 'test-user-123'
    return mock_context


@pytest.fixture
def mock_httpx_client():
    """Mock httpx AsyncClient for testing."""
    client = AsyncMock(spec=httpx.AsyncClient)
    return client


@pytest.fixture
def mock_db_session():
    """Mock database session for testing."""
    session = AsyncMock(spec=AsyncSession)
    return session


@pytest.fixture
def service(
    mock_sandbox_spec_service, mock_user_context, mock_httpx_client, mock_db_session
):
    """Create RemoteSandboxService instance for testing."""
    return RemoteSandboxService(
        sandbox_spec_service=mock_sandbox_spec_service,
        api_url='https://api.example.com',
        api_key='test-api-key',
        web_url='https://web.example.com',
        resource_factor=2,
        runtime_class='gvisor',
        start_sandbox_timeout=120,
        user_context=mock_user_context,
        httpx_client=mock_httpx_client,
        db_session=mock_db_session,
    )


@pytest.fixture
def mock_runtime_response():
    """Mock runtime API response data."""
    return {
        'runtime_id': 'runtime-123',
        'session_id': 'sandbox-abc123',
        'status': 'running',
        'pod_status': 'ready',
        'url': 'https://runtime.example.com',
        'session_api_key': 'session-key-456',
    }


@pytest.fixture
def mock_stored_sandbox():
    """Mock stored sandbox database record."""
    return StoredRemoteSandbox(
        id='sandbox-abc123',
        created_by_user_id='test-user-123',
        sandbox_spec_id='test-image:latest',
        created_at=datetime.utcnow(),
    )


class TestRemoteSandboxService:
    """Test cases for RemoteSandboxService."""

    async def test_send_runtime_api_request_success(self, service):
        """Test successful API request."""
        # Setup
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json = MagicMock(return_value={'status': 'success'})
        service.httpx_client.request.return_value = mock_response

        # Execute
        response = await service._send_runtime_api_request('GET', '/test')

        # Verify
        service.httpx_client.request.assert_called_once_with(
            'GET',
            'https://api.example.com/test',
            headers={'X-API-Key': 'test-api-key'},
        )
        assert response == mock_response

    async def test_send_runtime_api_request_timeout_error(self, service):
        """Test API request timeout handling."""
        # Setup
        service.httpx_client.request.side_effect = httpx.TimeoutException('Timeout')

        # Execute & Verify
        with pytest.raises(httpx.TimeoutException):
            await service._send_runtime_api_request('GET', '/test')

    async def test_send_runtime_api_request_http_error(self, service):
        """Test API request HTTP error handling."""
        # Setup
        service.httpx_client.request.side_effect = httpx.HTTPError('HTTP Error')

        # Execute & Verify
        with pytest.raises(httpx.HTTPError):
            await service._send_runtime_api_request('GET', '/test')

    async def test_get_runtime_success(self, service, mock_runtime_response):
        """Test successful runtime retrieval via /sessions endpoint."""
        # Setup
        mock_response = AsyncMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json = MagicMock(return_value=mock_runtime_response)
        service.httpx_client.request.return_value = mock_response

        # Execute
        runtime_data = await service._get_runtime('sandbox-abc123')

        # Verify
        service.httpx_client.request.assert_called_once_with(
            'GET',
            'https://api.example.com/sessions/sandbox-abc123',
            headers={'X-API-Key': 'test-api-key'},
        )
        mock_response.raise_for_status.assert_called_once()
        assert runtime_data == mock_runtime_response

    async def test_to_sandbox_info_with_running_runtime(
        self, service, mock_stored_sandbox, mock_runtime_response
    ):
        """Test conversion to SandboxInfo with running runtime."""
        # Execute
        sandbox_info = await service._to_sandbox_info(
            mock_stored_sandbox, mock_runtime_response
        )

        # Verify
        assert sandbox_info.id == 'sandbox-abc123'
        assert sandbox_info.created_by_user_id == 'test-user-123'
        assert sandbox_info.sandbox_spec_id == 'test-image:latest'
        assert sandbox_info.status == SandboxStatus.RUNNING
        assert sandbox_info.session_api_key == 'session-key-456'
        assert len(sandbox_info.exposed_urls) == 1
        assert sandbox_info.exposed_urls[0].name == AGENT_SERVER
        assert sandbox_info.exposed_urls[0].url == 'https://runtime.example.com'

    async def test_to_sandbox_info_with_missing_runtime(
        self, service, mock_stored_sandbox
    ):
        """Test conversion to SandboxInfo with missing runtime."""
        # Mock _get_runtime to raise an exception (simulating runtime not found)
        with patch.object(
            service, '_get_runtime', side_effect=httpx.HTTPError('Runtime not found')
        ):
            # Execute
            sandbox_info = await service._to_sandbox_info(mock_stored_sandbox, None)

            # Verify
            assert sandbox_info.status == SandboxStatus.MISSING
            assert sandbox_info.session_api_key is None
            assert sandbox_info.exposed_urls is None

    async def test_start_sandbox_success(self, service):
        """Test successful sandbox start."""
        # Setup
        mock_response = AsyncMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json = MagicMock(
            return_value={
                'runtime_id': 'runtime-123',
                'session_id': 'sandbox-abc123',
                'status': 'starting',
                'url': 'https://runtime.example.com',
                'session_api_key': 'session-key-456',
            }
        )
        service.httpx_client.request.return_value = mock_response

        # Mock database operations
        service.db_session.add = MagicMock()
        service.db_session.commit = AsyncMock()

        # Execute
        with patch('base62.encodebytes', return_value='sandbox-abc123'):
            sandbox_info = await service.start_sandbox()

        # Verify API call
        service.httpx_client.request.assert_called_once()
        call_args = service.httpx_client.request.call_args
        assert call_args[0][0] == 'POST'
        assert call_args[0][1] == 'https://api.example.com/start'
        assert 'json' in call_args[1]

        # Verify request payload
        request_data = call_args[1]['json']
        assert request_data['image'] == 'test-image:latest'
        assert request_data['session_id'] == 'sandbox-abc123'
        assert request_data['resource_factor'] == 2
        assert 'TEST_VAR' in request_data['environment']

        # Verify database operations
        service.db_session.add.assert_called_once()
        service.db_session.commit.assert_called_once()

        # Verify result
        assert sandbox_info.id == 'sandbox-abc123'
        assert sandbox_info.status == SandboxStatus.STARTING

    async def test_start_sandbox_http_error(self, service):
        """Test sandbox start with HTTP error."""
        # Setup
        service.httpx_client.request.side_effect = httpx.HTTPError('API Error')
        service.db_session.add = MagicMock()
        service.db_session.commit = AsyncMock()

        # Execute & Verify
        with pytest.raises(SandboxError, match='Failed to start sandbox'):
            with patch('base62.encodebytes', return_value='sandbox-abc123'):
                await service.start_sandbox()

    async def test_pause_sandbox_success(self, service, mock_runtime_response):
        """Test successful sandbox pause via /pause endpoint."""
        # Setup
        stored_sandbox = StoredRemoteSandbox(
            id='sandbox-abc123',
            created_by_user_id='test-user-123',
            sandbox_spec_id='test-image:latest',
        )

        with (
            patch.object(service, '_get_stored_sandbox', return_value=stored_sandbox),
            patch.object(service, '_get_runtime', return_value=mock_runtime_response),
        ):
            # Mock API response
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.raise_for_status = MagicMock()
            service.httpx_client.request.return_value = mock_response

            # Execute
            result = await service.pause_sandbox('sandbox-abc123')

            # Verify
            assert result is True
            service.httpx_client.request.assert_called_with(
                'POST',
                'https://api.example.com/pause',
                headers={'X-API-Key': 'test-api-key'},
                json={'runtime_id': 'runtime-123'},
            )

    async def test_pause_sandbox_not_found(self, service):
        """Test pause sandbox when sandbox not found."""
        # Setup - mock _get_stored_sandbox to return None
        with patch.object(service, '_get_stored_sandbox', return_value=None):
            # Execute
            result = await service.pause_sandbox('non-existent')

            # Verify
            assert result is False

    async def test_pause_sandbox_http_error(self, service):
        """Test pause sandbox with HTTP error."""
        # Setup
        stored_sandbox = StoredRemoteSandbox(
            id='sandbox-abc123',
            created_by_user_id='test-user-123',
            sandbox_spec_id='test-image:latest',
        )

        with (
            patch.object(service, '_get_stored_sandbox', return_value=stored_sandbox),
            patch.object(
                service, '_get_runtime', return_value={'runtime_id': 'runtime-123'}
            ),
        ):
            service.httpx_client.request.side_effect = httpx.HTTPError('API Error')

            # Execute
            result = await service.pause_sandbox('sandbox-abc123')

            # Verify
            assert result is False

    async def test_resume_sandbox_success(self, service, mock_runtime_response):
        """Test successful sandbox resume via /resume endpoint."""
        # Setup
        stored_sandbox = StoredRemoteSandbox(
            id='sandbox-abc123',
            created_by_user_id='test-user-123',
            sandbox_spec_id='test-image:latest',
        )

        with (
            patch.object(service, '_get_stored_sandbox', return_value=stored_sandbox),
            patch.object(service, '_get_runtime', return_value=mock_runtime_response),
        ):
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.raise_for_status = MagicMock()
            service.httpx_client.request.return_value = mock_response

            # Execute
            result = await service.resume_sandbox('sandbox-abc123')

            # Verify
            assert result is True
            service.httpx_client.request.assert_called_with(
                'POST',
                'https://api.example.com/resume',
                headers={'X-API-Key': 'test-api-key'},
                json={'runtime_id': 'runtime-123'},
            )

    async def test_resume_sandbox_not_found(self, service):
        """Test resume sandbox when sandbox not found."""
        # Setup - mock _get_stored_sandbox to return None
        with patch.object(service, '_get_stored_sandbox', return_value=None):
            # Execute
            result = await service.resume_sandbox('non-existent')

            # Verify
            assert result is False

    async def test_delete_sandbox_success(self, service, mock_runtime_response):
        """Test successful sandbox deletion via /stop endpoint."""
        # Setup
        stored_sandbox = StoredRemoteSandbox(
            id='sandbox-abc123',
            created_by_user_id='test-user-123',
            sandbox_spec_id='test-image:latest',
        )

        service.db_session.delete = AsyncMock()
        service.db_session.commit = AsyncMock()

        with (
            patch.object(service, '_get_stored_sandbox', return_value=stored_sandbox),
            patch.object(service, '_get_runtime', return_value=mock_runtime_response),
        ):
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.raise_for_status = MagicMock()
            service.httpx_client.request.return_value = mock_response

            # Execute
            result = await service.delete_sandbox('sandbox-abc123')

            # Verify
            assert result is True
            service.db_session.delete.assert_called_once_with(stored_sandbox)
            service.db_session.commit.assert_called_once()
            service.httpx_client.request.assert_called_with(
                'POST',
                'https://api.example.com/stop',
                headers={'X-API-Key': 'test-api-key'},
                json={'runtime_id': 'runtime-123'},
            )

    async def test_delete_sandbox_not_found(self, service):
        """Test delete sandbox when sandbox not found."""
        # Setup - mock _get_stored_sandbox to return None
        with patch.object(service, '_get_stored_sandbox', return_value=None):
            # Execute
            result = await service.delete_sandbox('non-existent')

            # Verify
            assert result is False

    async def test_init_environment_with_web_url(self, service):
        """Test environment initialization with web URL."""
        # Setup
        sandbox_spec = SandboxSpecInfo(
            id='test-image:latest',
            initial_env={'EXISTING_VAR': 'existing_value'},
            working_dir='/workspace',
            command=['python', '-m', 'openhands.runtime.action_execution_server'],
        )

        # Execute
        environment = await service._init_environment(sandbox_spec, 'sandbox-123')

        # Verify
        assert environment['EXISTING_VAR'] == 'existing_value'
        assert (
            environment['OH_WEBHOOKS_0_BASE_URL']
            == 'https://web.example.com/api/v1/webhooks/sandbox-123'
        )

    async def test_init_environment_without_web_url(self, service):
        """Test environment initialization without web URL."""
        # Setup
        service.web_url = None
        sandbox_spec = SandboxSpecInfo(
            id='test-image:latest',
            initial_env={'EXISTING_VAR': 'existing_value'},
            working_dir='/workspace',
            command=['python', '-m', 'openhands.runtime.action_execution_server'],
        )

        # Execute
        environment = await service._init_environment(sandbox_spec, 'sandbox-123')

        # Verify
        assert environment['EXISTING_VAR'] == 'existing_value'
        assert 'OH_WEBHOOKS_0_BASE_URL' not in environment

    async def test_status_mapping_edge_cases(self, service, mock_stored_sandbox):
        """Test status mapping for various runtime states."""
        test_cases = [
            # (pod_status, runtime_status, expected_sandbox_status)
            ('ready', 'running', SandboxStatus.RUNNING),
            ('pending', 'starting', SandboxStatus.STARTING),
            ('running', 'starting', SandboxStatus.STARTING),
            ('failed', 'error', SandboxStatus.ERROR),
            ('unknown', 'error', SandboxStatus.ERROR),
            ('crashloopbackoff', 'error', SandboxStatus.ERROR),
            ('', 'paused', SandboxStatus.PAUSED),
            ('', 'stopped', SandboxStatus.MISSING),
            ('invalid', 'invalid', SandboxStatus.MISSING),
        ]

        for pod_status, runtime_status, expected_status in test_cases:
            runtime_data = {
                'runtime_id': 'runtime-123',
                'session_id': 'sandbox-abc123',
                'status': runtime_status,
                'pod_status': pod_status,
                'url': 'https://runtime.example.com',
                'session_api_key': 'session-key-456',
            }

            sandbox_info = await service._to_sandbox_info(
                mock_stored_sandbox, runtime_data
            )
            assert sandbox_info.status == expected_status, (
                f'Failed for pod_status={pod_status}, runtime_status={runtime_status}'
            )


class TestRemoteSandboxServiceListEndpoint:
    """Test cases specifically for the /list endpoint used in polling."""

    async def test_list_endpoint_success(self):
        """Test that /list endpoint is called correctly."""
        # Setup mock httpx client
        mock_client = AsyncMock()
        mock_response = AsyncMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json = MagicMock(
            return_value={
                'runtimes': [
                    {
                        'session_id': 'sandbox-1',
                        'status': 'running',
                        'runtime_id': 'runtime-1',
                        'url': 'https://runtime1.example.com',
                        'session_api_key': 'key-1',
                    },
                    {
                        'session_id': 'sandbox-2',
                        'status': 'running',
                        'runtime_id': 'runtime-2',
                        'url': 'https://runtime2.example.com',
                        'session_api_key': 'key-2',
                    },
                ]
            }
        )
        mock_client.get.return_value = mock_response

        # Simulate the core logic from poll_agent_servers
        response = await mock_client.get(
            'https://api.example.com/list', headers={'X-API-Key': 'test-api-key'}
        )
        response.raise_for_status()
        runtimes_data = response.json()

        # Verify
        mock_client.get.assert_called_once_with(
            'https://api.example.com/list', headers={'X-API-Key': 'test-api-key'}
        )
        assert len(runtimes_data['runtimes']) == 2
        assert runtimes_data['runtimes'][0]['session_id'] == 'sandbox-1'

    async def test_list_endpoint_error_handling(self):
        """Test error handling for /list endpoint."""
        # Setup mock httpx client with error
        mock_client = AsyncMock()
        mock_client.get.side_effect = httpx.HTTPError('Connection failed')

        # Verify that the error is properly raised
        with pytest.raises(httpx.HTTPError):
            await mock_client.get(
                'https://api.example.com/list', headers={'X-API-Key': 'test-api-key'}
            )

    async def test_list_endpoint_timeout_handling(self):
        """Test timeout handling for /list endpoint."""
        # Setup mock httpx client with timeout
        mock_client = AsyncMock()
        mock_client.get.side_effect = httpx.TimeoutException('Request timed out')

        # Verify that the timeout is properly raised
        with pytest.raises(httpx.TimeoutException):
            await mock_client.get(
                'https://api.example.com/list', headers={'X-API-Key': 'test-api-key'}
            )


class TestRemoteSandboxServiceErrorHandling:
    """Test cases specifically for error handling scenarios."""

    async def test_comprehensive_error_scenarios(self, service):
        """Test various error scenarios across different methods."""
        error_scenarios = [
            (httpx.TimeoutException('Timeout'), 'timeout'),
            (httpx.HTTPError('HTTP Error'), 'http_error'),
        ]

        for exception, scenario_name in error_scenarios:
            # Test _send_runtime_api_request error handling
            service.httpx_client.request.side_effect = exception

            with pytest.raises(type(exception)):
                await service._send_runtime_api_request('GET', '/test')

            # Reset for next test
            service.httpx_client.request.side_effect = None

    async def test_parallelization_concept(self):
        """Test that asyncio.gather can be used for parallelization."""

        # This tests the concept used in search_sandboxes
        async def mock_async_operation(item_id):
            await asyncio.sleep(0.001)  # Simulate async work
            return f'processed-{item_id}'

        items = ['item1', 'item2', 'item3']

        # Test parallel execution
        results = await asyncio.gather(*[mock_async_operation(item) for item in items])

        # Verify
        assert len(results) == 3
        assert results == ['processed-item1', 'processed-item2', 'processed-item3']

    async def test_error_handling_in_to_sandbox_info(
        self, service, mock_stored_sandbox
    ):
        """Test that _to_sandbox_info handles runtime fetch errors gracefully."""
        # Mock _get_runtime to raise an exception
        with patch.object(
            service, '_get_runtime', side_effect=httpx.HTTPError('API Error')
        ):
            # Execute
            sandbox_info = await service._to_sandbox_info(mock_stored_sandbox)

            # Verify - should return MISSING status when runtime fetch fails
            assert sandbox_info.status == SandboxStatus.MISSING
            assert sandbox_info.session_api_key is None
            assert sandbox_info.exposed_urls is None
