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
        mock_client.return_value.version.return_value = {'Version': '20.10.0'}
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


def test_memory_limit_enforcement(mock_docker_client, config, event_stream):
    """Test that memory limits are enforced correctly in the Docker runtime.
    
    This test verifies that:
    1. A process that exceeds a low memory limit gets killed
    2. The same process runs successfully with a higher memory limit
    """
    # Test with low memory limit (128MB)
    config.sandbox.memory_limit = "128m"
    runtime_low_mem = DockerRuntime(config, event_stream, sid='test-low-mem')
    
    # Python script that will consume memory
    memory_hog_script = """
import numpy as np
import time

# Allocate a 256MB array (should exceed our 128MB limit)
data = np.zeros((256 * 1024 * 1024,), dtype=np.uint8)
time.sleep(1)  # Keep the array in memory
print("Memory allocation successful")
"""
    
    # Execute with low memory limit - should fail
    result_low = runtime_low_mem.execute_python(memory_hog_script)
    assert "MemoryError" in result_low.error or "Killed" in result_low.error, \
        "Process should have been killed or raised MemoryError with low memory limit"
    
    # Test with high memory limit (512MB)
    config.sandbox.memory_limit = "512m"
    runtime_high_mem = DockerRuntime(config, event_stream, sid='test-high-mem')
    
    # Execute with high memory limit - should succeed
    result_high = runtime_high_mem.execute_python(memory_hog_script)
    assert result_high.error is None, \
        "Process should have completed successfully with high memory limit"
    assert "Memory allocation successful" in result_high.output, \
        "Process should have completed memory allocation successfully"
