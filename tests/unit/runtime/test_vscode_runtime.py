# Unit tests for VsCodeRuntime

from unittest.mock import AsyncMock, Mock, patch

import pytest

from openhands.core.config import OpenHandsConfig
from openhands.events.action import CmdRunAction, FileReadAction
from openhands.events.observation import (
    CmdOutputObservation,
    ErrorObservation,
    FileReadObservation,
)
from openhands.events.stream import EventStream
from openhands.runtime.vscode.vscode_runtime import VsCodeRuntime


class TestVsCodeRuntimeConstructor:
    """Test VsCodeRuntime constructor and initialization."""

    def test_constructor_no_dependencies(self):
        """Test that VsCodeRuntime can be constructed without sio_server/socket_connection_id."""
        config = OpenHandsConfig()
        event_stream = Mock(spec=EventStream)

        # Should not raise any exceptions
        runtime = VsCodeRuntime(config=config, event_stream=event_stream)

        assert runtime.config is not None
        assert runtime.sid == 'default'
        assert runtime.plugins == []
        assert runtime.env_vars == {}
        assert runtime.sio_server is None
        assert runtime.socket_connection_id is None
        assert runtime._running_actions == {}
        assert runtime._server_url == 'http://localhost:3000'

    def test_constructor_with_optional_params(self):
        """Test constructor with optional parameters."""
        config = OpenHandsConfig()
        event_stream = Mock(spec=EventStream)

        runtime = VsCodeRuntime(
            config=config, event_stream=event_stream, sid='test_sid', plugins=[]
        )

        assert runtime.config is not None
        assert runtime.event_stream is not None
        assert runtime.sid == 'test_sid'


class TestVsCodeRuntimeDiscovery:
    """Test VSCode instance discovery system."""

    @pytest.fixture
    def runtime(self):
        config = OpenHandsConfig()
        event_stream = Mock(spec=EventStream)
        return VsCodeRuntime(config=config, event_stream=event_stream)

    @pytest.mark.asyncio
    async def test_discover_vscode_instances_success(self, runtime):
        """Test successful discovery of VSCode instances."""
        mock_response_data = [
            {
                'id': 'vscode-1',
                'name': 'VSCode Instance 1',
                'port': 3001,
                'status': 'active',
                'workspace': '/path/to/workspace1',
            },
            {
                'id': 'vscode-2',
                'name': 'VSCode Instance 2',
                'port': 3002,
                'status': 'active',
                'workspace': '/path/to/workspace2',
            },
        ]

        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_response_data)
            mock_get.return_value.__aenter__.return_value = mock_response

            instances = await runtime._get_available_vscode_instances()

            assert len(instances) == 2
            assert instances[0]['id'] == 'vscode-1'
            assert instances[1]['id'] == 'vscode-2'

    @pytest.mark.asyncio
    async def test_discover_vscode_instances_server_error(self, runtime):
        """Test discovery when server returns error."""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 500
            mock_get.return_value.__aenter__.return_value = mock_response

            instances = await runtime._get_available_vscode_instances()

            assert instances == []

    @pytest.mark.asyncio
    async def test_discover_vscode_instances_connection_error(self, runtime):
        """Test discovery when connection fails."""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.side_effect = Exception('Connection failed')

            instances = await runtime._get_available_vscode_instances()

            assert instances == []

    @pytest.mark.asyncio
    async def test_discovery_multiple_calls(self, runtime):
        """Test that multiple discovery calls work correctly."""
        mock_response_data = [{'id': 'vscode-1', 'port': 3001}]

        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_response_data)
            mock_get.return_value.__aenter__.return_value = mock_response

            # First call should make HTTP request
            instances1 = await runtime._get_available_vscode_instances()
            assert mock_get.call_count == 1
            assert len(instances1) == 1

            # Second call should make another HTTP request (no caching)
            instances2 = await runtime._get_available_vscode_instances()
            assert mock_get.call_count == 2  # Additional call made
            assert instances1 == instances2


class TestVsCodeRuntimeConnection:
    """Test VSCode connection management."""

    @pytest.fixture
    def runtime(self):
        config = OpenHandsConfig()
        event_stream = Mock(spec=EventStream)
        return VsCodeRuntime(config=config, event_stream=event_stream)

    @pytest.mark.asyncio
    async def test_validate_connection_success(self, runtime):
        """Test successful connection validation."""
        connection_id = 'vscode-1'

        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={'status': 'active'})
            mock_get.return_value.__aenter__.return_value = mock_response

            is_valid = await runtime._validate_vscode_connection(connection_id)

            assert is_valid is True

    @pytest.mark.asyncio
    async def test_validate_connection_failure(self, runtime):
        """Test connection validation failure."""
        connection_id = 'vscode-1'

        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.side_effect = Exception('Connection failed')

            is_valid = await runtime._validate_vscode_connection(connection_id)

            assert is_valid is False

    @pytest.mark.asyncio
    async def test_discover_and_connect_success(self, runtime):
        """Test successful connection establishment."""
        mock_instances = [
            {
                'id': 'vscode-1',
                'port': 3001,
                'status': 'active',
                'connection_id': 'conn-1',
            },
            {
                'id': 'vscode-2',
                'port': 3002,
                'status': 'active',
                'connection_id': 'conn-2',
            },
        ]

        with (
            patch.object(
                runtime, '_get_available_vscode_instances', return_value=mock_instances
            ),
            patch('openhands.server.shared.sio') as mock_sio,
        ):
            runtime.sio_server = mock_sio
            result = await runtime._discover_and_connect()

            assert result is True

    @pytest.mark.asyncio
    async def test_discover_and_connect_no_sio_server(self, runtime):
        """Test connection when sio_server import fails."""
        with patch(
            'openhands.server.shared.sio', side_effect=ImportError('Module not found')
        ):
            result = await runtime._discover_and_connect()

            assert result is False

    @pytest.mark.asyncio
    async def test_discover_and_connect_no_instances(self, runtime):
        """Test connection when no instances are discovered."""
        with (
            patch.object(runtime, '_get_available_vscode_instances', return_value=[]),
            patch('openhands.server.shared.sio') as mock_sio,
        ):
            runtime.sio_server = mock_sio
            result = await runtime._discover_and_connect()

            assert result is False


class TestVsCodeRuntimeActions:
    """Test action execution in VsCodeRuntime."""

    # FIXME: Action tests are currently skipped due to complex async/sync boundary issues.
    # The run_action() method is synchronous but calls async methods internally (_send_action_to_vscode).
    # This creates complex async mocking requirements for HTTP calls and Socket.IO operations,
    # causing tests to hang due to event loop conflicts. Need to properly mock all async operations
    # and handle the sync/async boundary correctly.

    @pytest.fixture
    def runtime(self):
        config = OpenHandsConfig()
        event_stream = Mock(spec=EventStream)
        runtime = VsCodeRuntime(config=config, event_stream=event_stream)
        runtime._current_connection = {'id': 'vscode-1', 'port': 3001}
        return runtime

    @pytest.mark.skip(
        reason='FIXME: Async/sync boundary mocking issues causing tests to hang'
    )
    def test_run_action_cmd_success(self, runtime):
        """Test successful command execution."""
        action = CmdRunAction(command="echo 'hello'")

        # Mock the connection setup
        runtime.socket_connection_id = 'test-connection'

        with (
            patch('aiohttp.ClientSession.post') as mock_post,
            patch.object(
                runtime,
                '_validate_vscode_connection',
                new_callable=AsyncMock,
                return_value=True,
            ),
        ):
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(
                return_value={'exit_code': 0, 'output': 'hello\n'}
            )
            mock_post.return_value.__aenter__.return_value = mock_response

            observation = runtime.run_action(action)

            assert isinstance(observation, CmdOutputObservation)
            assert observation.exit_code == 0
            assert observation.content == 'hello\n'

    @pytest.mark.skip(
        reason='FIXME: Async/sync boundary mocking issues causing tests to hang'
    )
    def test_run_action_file_read_success(self, runtime):
        """Test successful file read."""
        action = FileReadAction(path='/test/file.txt')

        # Mock the connection setup
        runtime.socket_connection_id = 'test-connection'

        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(
                return_value={'content': 'file content here'}
            )
            mock_post.return_value.__aenter__.return_value = mock_response

            observation = runtime.run_action(action)

            assert isinstance(observation, FileReadObservation)
            assert observation.content == 'file content here'

    @pytest.mark.skip(
        reason='FIXME: Async/sync boundary mocking issues causing tests to hang'
    )
    def test_run_action_connection_error(self, runtime):
        """Test action execution when connection fails."""
        action = CmdRunAction(command="echo 'hello'")

        # No connection setup - should trigger discovery and fail
        with patch.object(runtime, '_get_available_vscode_instances', return_value=[]):
            observation = runtime.run_action(action)

            assert isinstance(observation, ErrorObservation)
            assert 'No VSCode instances' in observation.content

    @pytest.mark.skip(
        reason='FIXME: Async/sync boundary mocking issues causing tests to hang'
    )
    def test_run_action_with_valid_connection(self, runtime):
        """Test action execution with a valid connection."""
        action = CmdRunAction(command="echo 'hello'")

        # Set up a valid connection
        runtime.socket_connection_id = 'test-connection'

        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(
                return_value={'exit_code': 0, 'output': 'hello\n'}
            )
            mock_post.return_value.__aenter__.return_value = mock_response

            observation = runtime.run_action(action)

            assert isinstance(observation, CmdOutputObservation)
            assert observation.exit_code == 0
            assert observation.content == 'hello\n'


class TestVsCodeRuntimeErrorHandling:
    """Test error handling and recovery in VsCodeRuntime."""

    @pytest.fixture
    def runtime(self):
        config = OpenHandsConfig()
        event_stream = Mock(spec=EventStream)
        return VsCodeRuntime(config=config, event_stream=event_stream)

    def test_comprehensive_error_messages(self, runtime):
        """Test that error messages are comprehensive and helpful."""
        action = CmdRunAction(command='test')

        with patch.object(runtime, '_discover_and_connect') as mock_discover:
            mock_discover.return_value = False  # Connection failed

            observation = runtime.run_action(action)

            assert isinstance(observation, ErrorObservation)
            assert 'No VSCode instances' in observation.content

    def test_recovery_logic(self, runtime):
        """Test recovery logic when connections fail."""
        # Set up initial connection
        runtime._current_connection = {'id': 'vscode-1', 'port': 3001}
        runtime.socket_connection_id = 'vscode-1'

        action = CmdRunAction(command='test')

        # Mock connection validation to fail first, then succeed
        with (
            patch.object(runtime, '_validate_vscode_connection') as mock_validate,
            patch.object(runtime, '_discover_and_connect') as mock_discover,
        ):
            # First validation fails (connection lost)
            mock_validate.return_value = False
            # Discovery succeeds with new connection
            mock_discover.return_value = True
            # Mock Socket.IO server directly
            runtime.sio_server = Mock()

            # This should trigger recovery
            runtime.run_action(action)

            # Should have attempted discovery (may be called multiple times during recovery)
            assert mock_discover.call_count >= 1


class TestVsCodeRuntimeIntegration:
    """Integration tests for VsCodeRuntime components."""

    @pytest.fixture
    def runtime(self):
        config = OpenHandsConfig()
        event_stream = Mock(spec=EventStream)
        return VsCodeRuntime(config=config, event_stream=event_stream)

    def test_full_workflow_success(self, runtime):
        """Test complete workflow from discovery to action execution."""
        mock_instances = [
            {
                'id': 'vscode-1',
                'port': 3001,
                'status': 'active',
                'connection_id': 'vscode-1',
            }
        ]
        action = CmdRunAction(command='pwd')

        with patch('aiohttp.ClientSession.get') as mock_get:
            # Mock discovery - return proper format with 'instances' key
            mock_discovery_response = AsyncMock()
            mock_discovery_response.status = 200
            mock_discovery_response.json = AsyncMock(return_value=mock_instances)

            # Mock Socket.IO server directly
            runtime.sio_server = Mock()

            # Set up mock responses
            mock_get.return_value.__aenter__.return_value = mock_discovery_response

            # Execute action - should trigger discovery workflow
            runtime.run_action(action)

            # Should have attempted discovery
            mock_get.assert_called()
            # Should have set socket connection ID
            assert runtime.socket_connection_id == 'vscode-1'
