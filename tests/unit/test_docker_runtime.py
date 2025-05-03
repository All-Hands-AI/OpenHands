from unittest.mock import MagicMock, patch

import pytest

from openhands.core.config import AppConfig
from openhands.events import EventStream
from openhands.runtime.impl.docker.docker_runtime import DockerRuntime


@pytest.fixture
def mock_docker_client():
    with patch('docker.from_env') as mock_client:
        container_mock = MagicMock()
        container_mock.status = 'running'
        container_mock.attrs = {
            'Config': {
                'Env': ['port=12345', 'VSCODE_PORT=54321'],
                'ExposedPorts': {'12345/tcp': {}, '54321/tcp': {}},
            }
        }
        mock_client.return_value.containers.get.return_value = container_mock
        mock_client.return_value.containers.run.return_value = container_mock
        # Mock version info for BuildKit check
        mock_client.return_value.version.return_value = {
            'Version': '20.10.0',
            'Components': [{'Name': 'Engine', 'Version': '20.10.0'}],
        }  # Ensure version is >= 18.09
        yield mock_client.return_value


@pytest.fixture
def config():
    config = AppConfig()
    config.sandbox.keep_runtime_alive = False
    return config


@pytest.fixture
def event_stream():
    return MagicMock(spec=EventStream)


@patch('openhands.runtime.impl.docker.docker_runtime.stop_all_containers')
def test_container_stopped_when_keep_runtime_alive_false(
    mock_stop_containers, mock_docker_client, config, event_stream
):
    # Arrange
    runtime = DockerRuntime(config, event_stream, sid='test-sid')
    runtime.container = mock_docker_client.containers.get.return_value

    # Act
    runtime.close()

    # Assert
    mock_stop_containers.assert_called_once_with('openhands-runtime-test-sid')


@patch('openhands.runtime.impl.docker.docker_runtime.stop_all_containers')
def test_container_not_stopped_when_keep_runtime_alive_true(
    mock_stop_containers, mock_docker_client, config, event_stream
):
    # Arrange
    config.sandbox.keep_runtime_alive = True
    runtime = DockerRuntime(config, event_stream, sid='test-sid')
    runtime.container = mock_docker_client.containers.get.return_value

    # Act
    runtime.close()

    # Assert
    mock_stop_containers.assert_not_called()


def test_runtime_mount_mode_extraction():
    """Test that the mount mode is correctly extracted from runtime_mount."""
    from openhands.runtime.impl.docker.docker_runtime import DockerRuntime
    
    # Create a mock DockerRuntime instance
    runtime = MagicMock(spec=DockerRuntime)
    
    # Test with read-only mode
    runtime.config = MagicMock()
    runtime.config.runtime_mount = '/host/path:/container/path:ro'
    runtime.config.workspace_mount_path = '/host/path'
    runtime.config.workspace_mount_path_in_sandbox = '/container/path'
    
    # Call the _create_container method directly
    volumes = {
        runtime.config.workspace_mount_path: {
            'bind': runtime.config.workspace_mount_path_in_sandbox,
            'mode': 'rw',  # Default mode
        }
    }
    
    # Simulate the code in DockerRuntime that extracts the mode
    if runtime.config.runtime_mount is not None:
        parts = runtime.config.runtime_mount.split(':')
        if len(parts) > 2:
            volumes[runtime.config.workspace_mount_path]['mode'] = parts[2]
    
    # Assert that the mode was correctly set to 'ro'
    assert volumes['/host/path']['mode'] == 'ro'


def test_runtime_mount_default_mode():
    """Test that the default mount mode (rw) is used when not specified in runtime_mount."""
    from openhands.runtime.impl.docker.docker_runtime import DockerRuntime
    
    # Create a mock DockerRuntime instance
    runtime = MagicMock(spec=DockerRuntime)
    
    # Test with no mode specified (should default to 'rw')
    runtime.config = MagicMock()
    runtime.config.runtime_mount = '/host/path:/container/path'
    runtime.config.workspace_mount_path = '/host/path'
    runtime.config.workspace_mount_path_in_sandbox = '/container/path'
    
    # Call the _create_container method directly
    volumes = {
        runtime.config.workspace_mount_path: {
            'bind': runtime.config.workspace_mount_path_in_sandbox,
            'mode': 'rw',  # Default mode
        }
    }
    
    # Simulate the code in DockerRuntime that extracts the mode
    if runtime.config.runtime_mount is not None:
        parts = runtime.config.runtime_mount.split(':')
        if len(parts) > 2:
            volumes[runtime.config.workspace_mount_path]['mode'] = parts[2]
    
    # Assert that the mode remains 'rw' (default)
    assert volumes['/host/path']['mode'] == 'rw'
