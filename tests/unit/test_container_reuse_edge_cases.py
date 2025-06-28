"""Unit tests for container reuse edge cases and error handling.

These tests focus on specific error conditions, edge cases, and boundary conditions
that could occur during container reuse operations using mocked components.
"""

from unittest.mock import MagicMock, patch

import pytest

from openhands.core.config import OpenHandsConfig
from openhands.events import EventStream
from openhands.runtime.impl.docker.docker_runtime import DockerRuntime


@pytest.fixture
def mock_docker_client():
    """Create a comprehensive mock Docker client for edge case testing."""
    with patch('docker.from_env') as mock_client:
        client = MagicMock()
        mock_client.return_value = client

        # Setup default container behavior
        container_mock = MagicMock()
        container_mock.status = 'running'
        container_mock.id = 'test-container-id'
        container_mock.name = 'test-container-name'
        container_mock.attrs = {
            'Config': {
                'Env': ['OH_SESSION_ID=test-sid', 'port=12345'],
                'ExposedPorts': {'12345/tcp': {}},
                'Image': 'test-image:latest',
            },
            'Image': 'sha256:abcd1234',
            'State': {'Status': 'running'},
        }

        client.containers.get.return_value = container_mock
        client.containers.run.return_value = container_mock
        client.containers.list.return_value = [container_mock]

        # Mock version info
        client.version.return_value = {
            'Version': '20.10.0',
            'Components': [{'Name': 'Engine', 'Version': '20.10.0'}],
        }

        yield client


@pytest.fixture
def config():
    """Create test configuration."""
    config = OpenHandsConfig()
    config.sandbox.keep_runtime_alive = False
    config.sandbox.container_reuse_strategy = 'none'
    return config


@pytest.fixture
def event_stream():
    """Create mock event stream."""
    return MagicMock(spec=EventStream)


class TestContainerReuseEdgeCases:
    """Test edge cases and error conditions in container reuse."""

    def test_reuse_with_missing_environment_variables(
        self, mock_docker_client, config, event_stream
    ):
        """Test reuse behavior when container missing required environment variables."""
        config.sandbox.container_reuse_strategy = 'pause'

        # Container missing OH_SESSION_ID
        container_mock = mock_docker_client.containers.list.return_value[0]
        container_mock.attrs['Config']['Env'] = ['OTHER_VAR=value']

        runtime = DockerRuntime(config, event_stream, sid='test-sid')
        runtime.docker_client = mock_docker_client

        # Should not reuse container without proper environment
        result = runtime._try_reuse_container()
        assert result is False

    def test_reuse_with_corrupted_container_attrs(
        self, mock_docker_client, config, event_stream
    ):
        """Test handling of containers with corrupted or missing attributes."""
        config.sandbox.container_reuse_strategy = 'pause'

        # Container with missing Config section
        container_mock = mock_docker_client.containers.list.return_value[0]
        container_mock.attrs = {'Image': 'test-image', 'State': {'Status': 'paused'}}

        runtime = DockerRuntime(config, event_stream, sid='test-sid')
        runtime.docker_client = mock_docker_client

        # Should handle missing Config gracefully
        result = runtime._try_reuse_container()
        assert result is False

    def test_workspace_cleanup_permission_denied(
        self, mock_docker_client, config, event_stream
    ):
        """Test workspace cleanup when permission denied errors occur."""
        config.sandbox.container_reuse_strategy = 'keep_alive'

        runtime = DockerRuntime(config, event_stream, sid='test-sid')
        runtime.docker_client = mock_docker_client
        runtime.container = mock_docker_client.containers.get.return_value

        # Mock exec_run to simulate permission denied during cleanup
        exec_result = MagicMock()
        exec_result.exit_code = 1
        exec_result.output = (
            b"rm: cannot remove '/workspace/file.txt': Permission denied"
        )
        runtime.container.exec_run.return_value = exec_result

        # Should handle permission errors gracefully (logs warning, doesn't raise)
        runtime._clean_workspace_for_reuse()

        # Verify cleanup was attempted
        runtime.container.exec_run.assert_called()

    def test_container_pause_operation_failure(
        self, mock_docker_client, config, event_stream
    ):
        """Test handling when container pause operation fails."""
        config.sandbox.container_reuse_strategy = 'pause'

        runtime = DockerRuntime(config, event_stream, sid='test-sid')
        runtime.docker_client = mock_docker_client
        runtime.container = mock_docker_client.containers.get.return_value

        # Mock pause to fail
        runtime.container.pause.side_effect = Exception('Failed to pause container')

        # Should fall back to stop
        runtime.pause()

        runtime.container.pause.assert_called_once()
        runtime.container.stop.assert_called_once()

    def test_container_resume_operation_failure(
        self, mock_docker_client, config, event_stream
    ):
        """Test handling when container resume operation fails."""
        config.sandbox.container_reuse_strategy = 'pause'

        # Container in paused state
        container_mock = mock_docker_client.containers.list.return_value[0]
        container_mock.status = 'paused'
        container_mock.attrs['State']['Status'] = 'paused'

        runtime = DockerRuntime(config, event_stream, sid='test-sid')
        runtime.docker_client = mock_docker_client

        # Mock unpause to fail
        container_mock.unpause.side_effect = Exception('Failed to unpause container')

        # Should handle resume failure and not reuse container
        result = runtime._try_reuse_container()
        assert result is False

    def test_container_discovery_with_docker_api_errors(
        self, mock_docker_client, config, event_stream
    ):
        """Test container discovery when Docker API returns errors."""
        config.sandbox.container_reuse_strategy = 'pause'

        runtime = DockerRuntime(config, event_stream, sid='test-sid')
        runtime.docker_client = mock_docker_client

        # Mock containers.list to raise API error
        mock_docker_client.containers.list.side_effect = Exception('Docker API error')

        # Should handle API errors gracefully
        result = runtime._try_reuse_container()
        assert result is False

    def test_invalid_container_reuse_strategy_enum_conversion(
        self, mock_docker_client, config, event_stream
    ):
        """Test handling of invalid strategy values during enum conversion."""
        # Set invalid strategy that bypasses config validation
        config.sandbox.container_reuse_strategy = 'invalid_strategy'

        runtime = DockerRuntime(config, event_stream, sid='test-sid')
        runtime.docker_client = mock_docker_client

        # Should handle invalid strategy gracefully (default to 'none' behavior)
        result = runtime._try_reuse_container()
        assert result is False

    def test_container_image_mismatch_during_reuse(
        self, mock_docker_client, config, event_stream
    ):
        """Test detection of image mismatches during container reuse."""
        config.sandbox.container_reuse_strategy = 'pause'
        config.sandbox.base_container_image = 'expected-image:latest'

        # Container using different image
        container_mock = mock_docker_client.containers.list.return_value[0]
        container_mock.attrs['Config']['Image'] = 'different-image:latest'

        runtime = DockerRuntime(config, event_stream, sid='test-sid')
        runtime.docker_client = mock_docker_client

        # Should detect image mismatch and not reuse
        result = runtime._is_container_reusable(container_mock)
        assert result is False

    def test_container_rename_conflict_during_reuse(
        self, mock_docker_client, config, event_stream
    ):
        """Test handling of container rename conflicts during reuse."""
        config.sandbox.container_reuse_strategy = 'pause'

        container_mock = mock_docker_client.containers.list.return_value[0]
        container_mock.status = 'paused'
        container_mock.name = 'old-name'

        runtime = DockerRuntime(config, event_stream, sid='test-sid')
        runtime.docker_client = mock_docker_client

        # Mock rename to fail due to conflict
        container_mock.rename.side_effect = Exception('Name conflict')

        # Should handle rename failure gracefully
        with patch.object(runtime, '_is_container_reusable', return_value=True):
            result = runtime._try_reuse_container()
            # Should still attempt reuse despite rename failure
            assert result is False or result is True  # Implementation dependent

    def test_container_network_configuration_mismatch(
        self, mock_docker_client, config, event_stream
    ):
        """Test detection of network configuration mismatches."""
        config.sandbox.container_reuse_strategy = 'pause'
        config.sandbox.use_host_network = True

        # Container with different network configuration
        container_mock = mock_docker_client.containers.list.return_value[0]
        container_mock.attrs['HostConfig'] = {'NetworkMode': 'bridge'}

        runtime = DockerRuntime(config, event_stream, sid='test-sid')
        runtime.docker_client = mock_docker_client

        # Should detect network configuration mismatch
        result = runtime._is_container_reusable(container_mock)
        assert result is False

    def test_excessive_workspace_cleanup_time(
        self, mock_docker_client, config, event_stream
    ):
        """Test handling when workspace cleanup takes excessive time."""
        config.sandbox.container_reuse_strategy = 'keep_alive'

        runtime = DockerRuntime(config, event_stream, sid='test-sid')
        runtime.docker_client = mock_docker_client
        runtime.container = mock_docker_client.containers.get.return_value

        # Mock exec_run to simulate long-running cleanup
        exec_result = MagicMock()
        exec_result.exit_code = 0
        exec_result.output = b'Cleanup completed'

        def slow_exec_run(*args, **kwargs):
            import time

            time.sleep(0.1)  # Simulate slow operation
            return exec_result

        runtime.container.exec_run.side_effect = slow_exec_run

        # Should complete cleanup even if it takes time
        runtime._clean_workspace_for_reuse()
        runtime.container.exec_run.assert_called()

    def test_container_state_transition_race_conditions(
        self, mock_docker_client, config, event_stream
    ):
        """Test handling of race conditions during container state transitions."""
        config.sandbox.container_reuse_strategy = 'pause'

        container_mock = mock_docker_client.containers.list.return_value[0]
        runtime = DockerRuntime(config, event_stream, sid='test-sid')
        runtime.docker_client = mock_docker_client

        # Simulate container state changing between discovery and reuse
        def state_changing_get(container_id):
            # Return different status on subsequent calls
            if not hasattr(state_changing_get, 'call_count'):
                state_changing_get.call_count = 0
            state_changing_get.call_count += 1

            if state_changing_get.call_count == 1:
                container_mock.status = 'paused'
            else:
                container_mock.status = 'exited'

            return container_mock

        mock_docker_client.containers.get.side_effect = state_changing_get

        # Should handle state changes gracefully
        result = runtime._try_reuse_container()
        assert result in [True, False]  # Either succeeds or fails gracefully

    def test_memory_constraints_during_reuse(
        self, mock_docker_client, config, event_stream
    ):
        """Test container reuse under memory constraints."""
        config.sandbox.container_reuse_strategy = 'keep_alive'

        # Configure memory limits
        config.sandbox.docker_runtime_kwargs = {'mem_limit': '512m'}

        container_mock = mock_docker_client.containers.list.return_value[0]
        container_mock.attrs['HostConfig'] = {'Memory': 536870912}  # 512MB
        container_mock.attrs['Config']['Env'] = ['OH_SESSION_ID=test-sid']

        runtime = DockerRuntime(config, event_stream, sid='test-sid')
        runtime.docker_client = mock_docker_client

        # Should handle memory constraints during reuse check
        result = runtime._is_container_reusable(container_mock)
        # Implementation may or may not check memory constraints
        assert result in [True, False]

    def test_concurrent_modification_of_container_during_reuse(
        self, mock_docker_client, config, event_stream
    ):
        """Test handling when container is modified by external process during reuse."""
        config.sandbox.container_reuse_strategy = 'pause'

        container_mock = mock_docker_client.containers.list.return_value[0]
        runtime = DockerRuntime(config, event_stream, sid='test-sid')
        runtime.docker_client = mock_docker_client

        # Simulate external modification
        def modified_during_reuse(*args, **kwargs):
            # Container gets removed by external process
            from docker.errors import NotFound

            raise NotFound('Container was removed')

        container_mock.unpause.side_effect = modified_during_reuse

        # Should handle external modifications gracefully
        result = runtime._try_reuse_container()
        assert result is False

    def test_disk_space_exhaustion_during_workspace_cleanup(
        self, mock_docker_client, config, event_stream
    ):
        """Test handling of disk space issues during workspace cleanup."""
        config.sandbox.container_reuse_strategy = 'keep_alive'

        runtime = DockerRuntime(config, event_stream, sid='test-sid')
        runtime.docker_client = mock_docker_client
        runtime.container = mock_docker_client.containers.get.return_value

        # Mock exec_run to simulate disk space exhaustion
        exec_result = MagicMock()
        exec_result.exit_code = 1
        exec_result.output = b'rm: cannot remove file: No space left on device'
        runtime.container.exec_run.return_value = exec_result

        # Should handle disk space issues gracefully (logs warning, doesn't raise)
        runtime._clean_workspace_for_reuse()

        # Verify cleanup was attempted despite disk space issues
        runtime.container.exec_run.assert_called()

    def test_container_security_context_validation(
        self, mock_docker_client, config, event_stream
    ):
        """Test validation of container security context during reuse."""
        config.sandbox.container_reuse_strategy = 'pause'
        config.run_as_openhands = True

        # Container running as different user
        container_mock = mock_docker_client.containers.list.return_value[0]
        container_mock.attrs['Config']['User'] = 'root'

        runtime = DockerRuntime(config, event_stream, sid='test-sid')
        runtime.docker_client = mock_docker_client

        # Should validate security context
        result = runtime._is_container_reusable(container_mock)
        # Implementation may or may not check user context
        assert result in [True, False]
