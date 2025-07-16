import os
from unittest.mock import MagicMock, patch

import docker
import pytest

from openhands.core.config import OpenHandsConfig
from openhands.events import EventStream
from openhands.runtime.impl.docker.containers import (
    ensure_warm_containers,
    get_warm_container,
    rename_container,
)
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


@patch('docker.from_env')
def test_get_warm_container(mock_docker_from_env):
    """Test that get_warm_container returns a warm container if one exists."""
    # Setup
    mock_client = MagicMock()
    mock_docker_from_env.return_value = mock_client

    mock_container = MagicMock()
    mock_container.name = 'openhands-runtime-warm-0'
    mock_client.containers.list.return_value = [mock_container]

    # Execute
    container = get_warm_container(mock_client, 'openhands-runtime-')

    # Assert
    assert container == mock_container
    mock_client.containers.list.assert_called_once_with(all=True)


@patch('docker.from_env')
def test_get_warm_container_none_available(mock_docker_from_env):
    """Test that get_warm_container returns None if no warm containers exist."""
    # Setup
    mock_client = MagicMock()
    mock_docker_from_env.return_value = mock_client

    mock_container = MagicMock()
    mock_container.name = 'openhands-runtime-regular'
    mock_client.containers.list.return_value = [mock_container]

    # Execute
    container = get_warm_container(mock_client, 'openhands-runtime-')

    # Assert
    assert container is None
    mock_client.containers.list.assert_called_once_with(all=True)


@patch('docker.from_env')
def test_rename_container(mock_docker_from_env):
    """Test that rename_container renames a container."""
    # Setup
    mock_container = MagicMock()

    # Execute
    result = rename_container(mock_container, 'new-name')

    # Assert
    assert result is True
    mock_container.rename.assert_called_once_with('new-name')


@patch('docker.from_env')
def test_rename_container_failure(mock_docker_from_env):
    """Test that rename_container handles failures."""
    # Setup
    mock_container = MagicMock()
    mock_container.rename.side_effect = Exception('Failed to rename')

    # Execute
    result = rename_container(mock_container, 'new-name')

    # Assert
    assert result is False
    mock_container.rename.assert_called_once_with('new-name')


@patch.dict(os.environ, {'NUM_WARM_CONTAINERS': '2'})
@patch('docker.from_env')
def test_ensure_warm_containers(mock_docker_from_env):
    """Test that ensure_warm_containers creates the right number of warm containers."""
    # Setup
    mock_client = MagicMock()
    mock_docker_from_env.return_value = mock_client

    # No existing warm containers
    mock_client.containers.list.return_value = []

    # Mock containers.get to raise NotFound
    mock_client.containers.get.side_effect = docker.errors.NotFound(
        'Container not found'
    )

    # Execute
    ensure_warm_containers(
        mock_client,
        'openhands-runtime-',
        'test-image',
        ['test-command'],
        {'ENV_VAR': 'value'},
        {},
    )

    # Assert
    assert mock_client.containers.run.call_count == 2
    mock_client.containers.run.assert_any_call(
        'test-image',
        command=['test-command'],
        entrypoint=[],
        network_mode=None,
        ports=None,
        working_dir='/openhands/code/',
        name='openhands-runtime-warm-0',
        detach=True,
        environment={'ENV_VAR': 'value'},
        volumes={},
        device_requests=None,
    )
    mock_client.containers.run.assert_any_call(
        'test-image',
        command=['test-command'],
        entrypoint=[],
        network_mode=None,
        ports=None,
        working_dir='/openhands/code/',
        name='openhands-runtime-warm-1',
        detach=True,
        environment={'ENV_VAR': 'value'},
        volumes={},
        device_requests=None,
    )


@patch.dict(os.environ, {'NUM_WARM_CONTAINERS': '1'})
@patch('openhands.runtime.impl.docker.containers.get_warm_container')
@patch('openhands.runtime.impl.docker.docker_runtime.rename_container')
@patch('openhands.runtime.impl.docker.docker_runtime.ensure_warm_containers')
@patch('openhands.runtime.impl.docker.docker_runtime.call_sync_from_async')
@pytest.mark.asyncio
async def test_connect_with_warm_container(
    mock_call_sync_from_async,
    mock_ensure_warm_containers,
    mock_rename_container,
    mock_get_warm_container,
    mock_docker_client,
    config,
    event_stream,
):
    """Test that connect uses a warm container if available."""
    # Setup
    runtime = DockerRuntime(config, event_stream, sid='test-sid')

    # Mock container not found for the specific sid and other calls
    warm_container = MagicMock()
    warm_container.name = 'openhands-runtime-warm-0'

    # Set up all the side effects for call_sync_from_async
    mock_call_sync_from_async.side_effect = [
        docker.errors.NotFound('Container not found'),  # For _attach_to_container
        warm_container,  # For get_warm_container
        True,  # For rename_container
        None,  # For _update_container_attributes
        None,  # For ensure_warm_containers
        None,  # For wait_until_alive
        None,  # For setup_initial_env
    ]

    # Mock finding a warm container
    mock_get_warm_container.return_value = warm_container

    # Mock successful rename
    mock_rename_container.return_value = True

    # Mock container attributes update
    runtime._update_container_attributes = MagicMock()

    # Mock wait_until_alive
    runtime.wait_until_alive = MagicMock()

    # Mock setup_initial_env
    runtime.setup_initial_env = MagicMock()

    # Execute
    await runtime.connect()

    # Assert
    # We don't check if get_warm_container was called since we're mocking call_sync_from_async
    mock_rename_container.assert_called_once_with(
        warm_container, 'openhands-runtime-test-sid'
    )
    assert runtime.container == warm_container
    runtime._update_container_attributes.assert_called_once()
    mock_ensure_warm_containers.assert_called_once()


@patch.dict(os.environ, {'NUM_WARM_CONTAINERS': '1'})
@patch('openhands.runtime.impl.docker.containers.get_warm_container')
@patch('openhands.runtime.impl.docker.docker_runtime.ensure_warm_containers')
@patch('openhands.runtime.impl.docker.docker_runtime.call_sync_from_async')
@pytest.mark.asyncio
async def test_connect_no_warm_container(
    mock_call_sync_from_async,
    mock_ensure_warm_containers,
    mock_get_warm_container,
    mock_docker_client,
    config,
    event_stream,
):
    """Test that connect creates a new container if no warm container is available."""
    # Setup
    runtime = DockerRuntime(config, event_stream, sid='test-sid')

    # Mock container not found for the specific sid and other calls
    # Set up all the side effects for call_sync_from_async
    mock_call_sync_from_async.side_effect = [
        docker.errors.NotFound('Container not found'),  # For _attach_to_container
        None,  # For get_warm_container
        None,  # For maybe_build_runtime_container_image
        None,  # For init_container
        None,  # For ensure_warm_containers
        None,  # For wait_until_alive
        None,  # For setup_initial_env
    ]

    # Mock no warm container found
    mock_get_warm_container.return_value = None

    # Mock container creation
    runtime.maybe_build_runtime_container_image = MagicMock()
    runtime.init_container = MagicMock()

    # Mock wait_until_alive
    runtime.wait_until_alive = MagicMock()

    # Mock setup_initial_env
    runtime.setup_initial_env = MagicMock()

    # Execute
    await runtime.connect()

    # Assert
    # We don't check if get_warm_container was called since we're mocking call_sync_from_async
    runtime.maybe_build_runtime_container_image.assert_called_once()
    runtime.init_container.assert_called_once()
    mock_ensure_warm_containers.assert_called_once()
