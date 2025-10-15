"""Tests for ProcessSandboxService."""

import os
import tempfile
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from openhands.app_server.sandbox.process_sandbox_service import (
    ProcessInfo,
    ProcessSandboxService,
    ProcessSandboxServiceInjector,
)
from openhands.app_server.sandbox.sandbox_models import SandboxStatus


class MockSandboxSpec:
    """Mock sandbox specification."""

    def __init__(self):
        self.id = 'test-spec'
        self.initial_env = {'TEST_VAR': 'test_value'}
        self.plugins = []


class MockSandboxSpecService:
    """Mock sandbox spec service."""

    async def get_default_sandbox_spec(self):
        return MockSandboxSpec()

    async def get_sandbox_spec(self, spec_id: str):
        if spec_id == 'test-spec':
            return MockSandboxSpec()
        return None


@pytest.fixture
def mock_httpx_client():
    """Mock httpx client."""
    client = AsyncMock(spec=httpx.AsyncClient)
    return client


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def process_sandbox_service(mock_httpx_client, temp_dir):
    """Create a ProcessSandboxService instance for testing."""
    return ProcessSandboxService(
        sandbox_spec_service=MockSandboxSpecService(),
        base_working_dir=temp_dir,
        base_port=9000,
        python_executable='python',
        action_server_module='openhands.runtime.action_execution_server',
        default_user='testuser',
        health_check_path='/alive',
        httpx_client=mock_httpx_client,
    )


class TestProcessSandboxService:
    """Test cases for ProcessSandboxService."""

    def test_find_unused_port(self, process_sandbox_service):
        """Test finding an unused port."""
        port = process_sandbox_service._find_unused_port()
        assert port >= process_sandbox_service.base_port
        assert port < process_sandbox_service.base_port + 10000

    @patch('pwd.getpwnam')
    def test_get_user_info_existing_user(self, mock_getpwnam, process_sandbox_service):
        """Test getting user info for existing user."""
        mock_user = MagicMock()
        mock_user.pw_uid = 1000
        mock_user.pw_gid = 1000
        mock_getpwnam.return_value = mock_user

        uid, gid = process_sandbox_service._get_user_info('testuser')
        assert uid == 1000
        assert gid == 1000

    @patch('pwd.getpwnam')
    @patch('os.getuid')
    @patch('os.getgid')
    def test_get_user_info_nonexistent_user(
        self, mock_getgid, mock_getuid, mock_getpwnam, process_sandbox_service
    ):
        """Test getting user info for non-existent user."""
        mock_getpwnam.side_effect = KeyError('User not found')
        mock_getuid.return_value = 1001
        mock_getgid.return_value = 1001

        uid, gid = process_sandbox_service._get_user_info('nonexistent')
        assert uid == 1001
        assert gid == 1001

    @patch('os.makedirs')
    @patch('os.chown')
    @patch('os.chmod')
    def test_create_sandbox_directory(
        self, mock_chmod, mock_chown, mock_makedirs, process_sandbox_service
    ):
        """Test creating a sandbox directory."""
        with patch.object(
            process_sandbox_service, '_get_user_info', return_value=(1000, 1000)
        ):
            sandbox_dir = process_sandbox_service._create_sandbox_directory(
                'test-id', 'testuser'
            )

            expected_dir = os.path.join(
                process_sandbox_service.base_working_dir, 'test-id'
            )
            assert sandbox_dir == expected_dir

            mock_makedirs.assert_called_once_with(expected_dir, exist_ok=True)
            mock_chown.assert_called_once_with(expected_dir, 1000, 1000)
            mock_chmod.assert_called_once_with(expected_dir, 0o755)

    @pytest.mark.asyncio
    async def test_wait_for_server_ready_success(self, process_sandbox_service):
        """Test waiting for server to be ready - success case."""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'status': 'ok'}
        process_sandbox_service.httpx_client.get.return_value = mock_response

        result = await process_sandbox_service._wait_for_server_ready(9000, timeout=1)
        assert result is True

    @pytest.mark.asyncio
    async def test_wait_for_server_ready_timeout(self, process_sandbox_service):
        """Test waiting for server to be ready - timeout case."""
        # Mock failed response
        process_sandbox_service.httpx_client.get.side_effect = Exception(
            'Connection failed'
        )

        result = await process_sandbox_service._wait_for_server_ready(9000, timeout=1)
        assert result is False

    @patch('psutil.Process')
    def test_get_process_status_running(
        self, mock_process_class, process_sandbox_service
    ):
        """Test getting process status for running process."""
        mock_process = MagicMock()
        mock_process.is_running.return_value = True
        mock_process.status.return_value = 'running'
        mock_process_class.return_value = mock_process

        process_info = ProcessInfo(
            pid=1234,
            port=9000,
            user='testuser',
            working_dir='/tmp/test',
            session_api_key='test-key',
            created_at=datetime.now(),
            sandbox_spec_id='test-spec',
        )

        status = process_sandbox_service._get_process_status(process_info)
        assert status == SandboxStatus.RUNNING

    @patch('psutil.Process')
    def test_get_process_status_missing(
        self, mock_process_class, process_sandbox_service
    ):
        """Test getting process status for missing process."""
        import psutil

        mock_process_class.side_effect = psutil.NoSuchProcess(1234)

        process_info = ProcessInfo(
            pid=1234,
            port=9000,
            user='testuser',
            working_dir='/tmp/test',
            session_api_key='test-key',
            created_at=datetime.now(),
            sandbox_spec_id='test-spec',
        )

        status = process_sandbox_service._get_process_status(process_info)
        assert status == SandboxStatus.MISSING

    @pytest.mark.asyncio
    async def test_search_sandboxes_empty(self, process_sandbox_service):
        """Test searching sandboxes when none exist."""
        result = await process_sandbox_service.search_sandboxes()

        assert len(result.items) == 0
        assert result.next_page_id is None

    @pytest.mark.asyncio
    async def test_get_sandbox_not_found(self, process_sandbox_service):
        """Test getting a sandbox that doesn't exist."""
        result = await process_sandbox_service.get_sandbox('nonexistent')
        assert result is None

    @pytest.mark.asyncio
    async def test_resume_sandbox_not_found(self, process_sandbox_service):
        """Test resuming a sandbox that doesn't exist."""
        result = await process_sandbox_service.resume_sandbox('nonexistent')
        assert result is False

    @pytest.mark.asyncio
    async def test_pause_sandbox_not_found(self, process_sandbox_service):
        """Test pausing a sandbox that doesn't exist."""
        result = await process_sandbox_service.pause_sandbox('nonexistent')
        assert result is False

    @pytest.mark.asyncio
    async def test_delete_sandbox_not_found(self, process_sandbox_service):
        """Test deleting a sandbox that doesn't exist."""
        result = await process_sandbox_service.delete_sandbox('nonexistent')
        assert result is False


class TestProcessSandboxServiceInjector:
    """Test cases for ProcessSandboxServiceInjector."""

    def test_default_values(self):
        """Test default configuration values."""
        injector = ProcessSandboxServiceInjector()

        assert injector.base_working_dir == '/tmp/openhands-sandboxes'
        assert injector.base_port == 8000
        assert injector.default_user == 'openhands'
        assert injector.health_check_path == '/alive'
        assert (
            injector.action_server_module == 'openhands.runtime.action_execution_server'
        )

    def test_custom_values(self):
        """Test custom configuration values."""
        injector = ProcessSandboxServiceInjector(
            base_working_dir='/custom/path',
            base_port=9000,
            default_user='custom_user',
            health_check_path='/health',
        )

        assert injector.base_working_dir == '/custom/path'
        assert injector.base_port == 9000
        assert injector.default_user == 'custom_user'
        assert injector.health_check_path == '/health'
