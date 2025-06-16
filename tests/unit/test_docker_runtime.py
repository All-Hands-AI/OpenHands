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


# Container Reuse Strategy Tests


def test_container_reuse_strategy_none(mock_docker_client, config, event_stream):
    """Test that container reuse is disabled with 'none' strategy."""
    config.sandbox.container_reuse_strategy = 'none'
    runtime = DockerRuntime(config, event_stream, sid='test-sid')
    runtime.docker_client = mock_docker_client

    # Test _try_reuse_container returns False for 'none' strategy
    result = runtime._try_reuse_container()
    assert result is False


def test_container_reuse_strategy_pause(mock_docker_client, config, event_stream):
    """Test pause strategy behavior in container reuse."""
    config.sandbox.container_reuse_strategy = 'pause'
    runtime = DockerRuntime(config, event_stream, sid='test-sid')
    runtime.docker_client = mock_docker_client
    runtime.container = mock_docker_client.containers.get.return_value

    # Test pause behavior
    runtime.pause()
    runtime.container.pause.assert_called_once()


def test_container_reuse_strategy_pause_fallback(
    mock_docker_client, config, event_stream
):
    """Test pause strategy falls back to stop when pause fails."""
    config.sandbox.container_reuse_strategy = 'pause'
    runtime = DockerRuntime(config, event_stream, sid='test-sid')
    runtime.docker_client = mock_docker_client
    runtime.container = mock_docker_client.containers.get.return_value

    # Mock pause to raise an exception
    runtime.container.pause.side_effect = Exception('Pause failed')

    # Test pause behavior with fallback
    runtime.pause()
    runtime.container.pause.assert_called_once()
    runtime.container.stop.assert_called_once()


def test_container_reuse_strategy_keep_alive(mock_docker_client, config, event_stream):
    """Test keep_alive strategy behavior."""
    config.sandbox.container_reuse_strategy = 'keep_alive'
    runtime = DockerRuntime(config, event_stream, sid='test-sid')
    runtime.docker_client = mock_docker_client
    runtime.container = mock_docker_client.containers.get.return_value

    # Mock _clean_workspace_for_reuse method
    runtime._clean_workspace_for_reuse = MagicMock()

    # Test pause behavior for keep_alive strategy
    runtime.pause()
    runtime._clean_workspace_for_reuse.assert_called_once()
    runtime.container.pause.assert_not_called()
    runtime.container.stop.assert_not_called()


def test_container_resume_pause_strategy(mock_docker_client, config, event_stream):
    """Test resume behavior for pause strategy."""
    config.sandbox.container_reuse_strategy = 'pause'
    runtime = DockerRuntime(config, event_stream, sid='test-sid')
    runtime.docker_client = mock_docker_client
    runtime.container = mock_docker_client.containers.get.return_value
    runtime.container.status = 'paused'

    # Mock wait_until_alive to avoid network calls
    runtime.wait_until_alive = MagicMock()

    # Test resume behavior
    runtime.resume()
    runtime.container.unpause.assert_called_once()


def test_container_resume_keep_alive_strategy(mock_docker_client, config, event_stream):
    """Test resume behavior for keep_alive strategy."""
    config.sandbox.container_reuse_strategy = 'keep_alive'
    runtime = DockerRuntime(config, event_stream, sid='test-sid')
    runtime.docker_client = mock_docker_client
    runtime.container = mock_docker_client.containers.get.return_value
    runtime.container.status = 'running'

    # Mock wait_until_alive to avoid network calls
    runtime.wait_until_alive = MagicMock()

    # Test resume behavior
    runtime.resume()
    # Container should already be running, no start call needed
    runtime.container.start.assert_not_called()


def test_is_container_reusable_compatible_image(
    mock_docker_client, config, event_stream
):
    """Test container reusability check with compatible image."""
    runtime = DockerRuntime(config, event_stream, sid='test-sid')
    runtime.runtime_container_image = 'test-image:latest'

    # Mock container with compatible configuration
    mock_container = MagicMock()
    mock_container.attrs = {'Config': {'Image': 'test-image:latest'}}
    mock_container.status = 'exited'

    result = runtime._is_container_reusable(mock_container)
    assert result is True


def test_is_container_reusable_incompatible_image(
    mock_docker_client, config, event_stream
):
    """Test container reusability check with incompatible image."""
    runtime = DockerRuntime(config, event_stream, sid='test-sid')
    runtime.runtime_container_image = 'test-image:latest'

    # Mock container with incompatible configuration
    mock_container = MagicMock()
    mock_container.attrs = {'Config': {'Image': 'different-image:latest'}}
    mock_container.status = 'exited'

    result = runtime._is_container_reusable(mock_container)
    assert result is False


def test_is_container_reusable_running_container(
    mock_docker_client, config, event_stream
):
    """Test container reusability check with running container."""
    runtime = DockerRuntime(config, event_stream, sid='test-sid')
    runtime.runtime_container_image = 'test-image:latest'

    # Mock container that's currently running
    mock_container = MagicMock()
    mock_container.attrs = {'Config': {'Image': 'test-image:latest'}}
    mock_container.status = 'running'

    result = runtime._is_container_reusable(mock_container)
    assert result is False
