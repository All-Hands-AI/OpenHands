from unittest.mock import MagicMock, patch

import pytest

from openhands.core.config import OpenHandsConfig
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
    config = OpenHandsConfig()
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


def test_volumes_mode_extraction():
    """Test that the mount mode is correctly extracted from sandbox.volumes."""
    import os

    from openhands.runtime.impl.docker.docker_runtime import DockerRuntime

    # Create a DockerRuntime instance with a mock config
    runtime = DockerRuntime.__new__(DockerRuntime)
    runtime.config = MagicMock()
    runtime.config.sandbox.volumes = '/host/path:/container/path:ro'
    runtime.config.workspace_mount_path = '/host/path'
    runtime.config.workspace_mount_path_in_sandbox = '/container/path'

    # Call the actual method that processes volumes
    volumes = runtime._process_volumes()

    # Assert that the mode was correctly set to 'ro'
    assert volumes[os.path.abspath('/host/path')]['mode'] == 'ro'


# This test has been replaced by test_volumes_multiple_mounts


def test_volumes_multiple_mounts():
    """Test that multiple mounts in sandbox.volumes are correctly processed."""
    import os

    from openhands.runtime.impl.docker.docker_runtime import DockerRuntime

    # Create a DockerRuntime instance with a mock config
    runtime = DockerRuntime.__new__(DockerRuntime)
    runtime.config = MagicMock()
    runtime.config.runtime_mount = None
    runtime.config.sandbox.volumes = (
        '/host/path1:/container/path1,/host/path2:/container/path2:ro'
    )
    runtime.config.workspace_mount_path = '/host/path1'
    runtime.config.workspace_mount_path_in_sandbox = '/container/path1'

    # Call the actual method that processes volumes
    volumes = runtime._process_volumes()

    # Assert that both mounts were processed correctly
    assert len(volumes) == 2
    assert volumes[os.path.abspath('/host/path1')]['bind'] == '/container/path1'
    assert volumes[os.path.abspath('/host/path1')]['mode'] == 'rw'  # Default mode
    assert volumes[os.path.abspath('/host/path2')]['bind'] == '/container/path2'
    assert volumes[os.path.abspath('/host/path2')]['mode'] == 'ro'  # Specified mode


def test_multiple_volumes():
    """Test that multiple volumes are correctly processed."""
    import os

    from openhands.runtime.impl.docker.docker_runtime import DockerRuntime

    # Create a DockerRuntime instance with a mock config
    runtime = DockerRuntime.__new__(DockerRuntime)
    runtime.config = MagicMock()
    runtime.config.sandbox.volumes = '/host/path1:/container/path1,/host/path2:/container/path2,/host/path3:/container/path3:ro'
    runtime.config.workspace_mount_path = '/host/path1'
    runtime.config.workspace_mount_path_in_sandbox = '/container/path1'

    # Call the actual method that processes volumes
    volumes = runtime._process_volumes()

    # Assert that all mounts were processed correctly
    assert len(volumes) == 3
    assert volumes[os.path.abspath('/host/path1')]['bind'] == '/container/path1'
    assert volumes[os.path.abspath('/host/path1')]['mode'] == 'rw'
    assert volumes[os.path.abspath('/host/path2')]['bind'] == '/container/path2'
    assert volumes[os.path.abspath('/host/path2')]['mode'] == 'rw'
    assert volumes[os.path.abspath('/host/path3')]['bind'] == '/container/path3'
    assert volumes[os.path.abspath('/host/path3')]['mode'] == 'ro'


def test_volumes_default_mode():
    """Test that the default mount mode (rw) is used when not specified in sandbox.volumes."""
    import os

    from openhands.runtime.impl.docker.docker_runtime import DockerRuntime

    # Create a DockerRuntime instance with a mock config
    runtime = DockerRuntime.__new__(DockerRuntime)
    runtime.config = MagicMock()
    runtime.config.sandbox.volumes = '/host/path:/container/path'
    runtime.config.workspace_mount_path = '/host/path'
    runtime.config.workspace_mount_path_in_sandbox = '/container/path'

    # Call the actual method that processes volumes
    volumes = runtime._process_volumes()

    # Assert that the mode remains 'rw' (default)
    assert volumes[os.path.abspath('/host/path')]['mode'] == 'rw'


@patch('os.path.exists')
@patch('openhands.runtime.impl.docker.docker_runtime.DockerRuntime._init_docker_client')
def test_docker_socket_mounting_enabled_socket_exists(
    mock_init_docker, mock_exists, config, event_stream
):
    """Test that Docker socket is mounted when enabled and socket exists."""
    # Arrange
    mock_docker_client = MagicMock()
    mock_docker_client.version.return_value = {
        'Version': '20.10.0',
        'Components': [{'Name': 'Engine', 'Version': '20.10.0'}],
    }
    mock_init_docker.return_value = mock_docker_client
    mock_exists.return_value = True
    config.sandbox.mount_docker_socket = True
    runtime = DockerRuntime(config, event_stream, sid='test-sid')
    runtime.log = MagicMock()

    # Mock the _process_volumes method to return empty dict
    runtime._process_volumes = MagicMock(return_value={})

    # Mock other required methods and attributes
    runtime._find_available_port = MagicMock(side_effect=[30000, 40000, 50000, 55000])
    runtime.get_action_execution_server_startup_command = MagicMock(
        return_value='test-command'
    )
    runtime.set_runtime_status = MagicMock()
    runtime.initial_env_vars = {}
    runtime._vscode_enabled = False  # Mock the private attribute
    runtime.runtime_container_image = 'test-image'

    # Act
    runtime.init_container()

    # Assert
    mock_exists.assert_called_with('/var/run/docker.sock')
    runtime.log.assert_any_call(
        'warning',
        'Mounting Docker socket to enable Docker-in-Docker functionality. '
        'SECURITY WARNING: This grants container access to the host Docker daemon '
        'with root-equivalent privileges. Use only in trusted environments.',
    )

    # Check that docker.containers.run was called with the Docker socket mounted
    call_args = mock_docker_client.containers.run.call_args
    volumes_arg = call_args[1]['volumes']
    assert '/var/run/docker.sock' in volumes_arg
    assert volumes_arg['/var/run/docker.sock']['bind'] == '/var/run/docker.sock'
    assert volumes_arg['/var/run/docker.sock']['mode'] == 'rw'


@patch('os.path.exists')
@patch('openhands.runtime.impl.docker.docker_runtime.DockerRuntime._init_docker_client')
def test_docker_socket_mounting_enabled_socket_not_exists(
    mock_init_docker, mock_exists, config, event_stream
):
    """Test that warning is logged when Docker socket mounting is enabled but socket doesn't exist."""
    # Arrange
    mock_docker_client = MagicMock()
    mock_docker_client.version.return_value = {
        'Version': '20.10.0',
        'Components': [{'Name': 'Engine', 'Version': '20.10.0'}],
    }
    mock_init_docker.return_value = mock_docker_client
    mock_exists.return_value = False
    config.sandbox.mount_docker_socket = True
    runtime = DockerRuntime(config, event_stream, sid='test-sid')
    runtime.log = MagicMock()

    # Mock the _process_volumes method to return empty dict
    runtime._process_volumes = MagicMock(return_value={})

    # Mock other required methods and attributes
    runtime._find_available_port = MagicMock(side_effect=[30000, 40000, 50000, 55000])
    runtime.get_action_execution_server_startup_command = MagicMock(
        return_value='test-command'
    )
    runtime.set_runtime_status = MagicMock()
    runtime.initial_env_vars = {}
    runtime._vscode_enabled = False  # Mock the private attribute
    runtime.runtime_container_image = 'test-image'

    # Act
    runtime.init_container()

    # Assert
    mock_exists.assert_called_with('/var/run/docker.sock')
    runtime.log.assert_any_call(
        'warning',
        'Docker socket mounting requested but /var/run/docker.sock not found on host. '
        'Docker-in-Docker functionality will not be available.',
    )

    # Check that docker.containers.run was called without the Docker socket mounted
    call_args = mock_docker_client.containers.run.call_args
    assert call_args is not None, 'docker.containers.run should have been called'
    volumes_arg = call_args[1]['volumes']
    assert '/var/run/docker.sock' not in volumes_arg


@patch('openhands.runtime.impl.docker.docker_runtime.DockerRuntime._init_docker_client')
def test_docker_socket_mounting_disabled(mock_init_docker, config, event_stream):
    """Test that Docker socket is not mounted when disabled."""
    # Arrange
    mock_docker_client = MagicMock()
    mock_docker_client.version.return_value = {
        'Version': '20.10.0',
        'Components': [{'Name': 'Engine', 'Version': '20.10.0'}],
    }
    mock_init_docker.return_value = mock_docker_client
    config.sandbox.mount_docker_socket = False
    runtime = DockerRuntime(config, event_stream, sid='test-sid')
    runtime.log = MagicMock()

    # Mock the _process_volumes method to return empty dict
    runtime._process_volumes = MagicMock(return_value={})

    # Mock other required methods and attributes
    runtime._find_available_port = MagicMock(side_effect=[30000, 40000, 50000, 55000])
    runtime.get_action_execution_server_startup_command = MagicMock(
        return_value='test-command'
    )
    runtime.set_runtime_status = MagicMock()
    runtime.initial_env_vars = {}
    runtime._vscode_enabled = False  # Mock the private attribute
    runtime.runtime_container_image = 'test-image'

    # Act
    runtime.init_container()

    # Assert
    # Check that docker.containers.run was called without the Docker socket mounted
    call_args = mock_docker_client.containers.run.call_args
    assert call_args is not None, 'docker.containers.run should have been called'
    volumes_arg = call_args[1]['volumes']
    assert '/var/run/docker.sock' not in volumes_arg
