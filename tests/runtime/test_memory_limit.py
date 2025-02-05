import pytest
from openhands.core.config import AppConfig
from openhands.events import EventStream
from openhands.runtime.impl.docker.docker_runtime import DockerRuntime


@pytest.fixture
def config():
    config = AppConfig()
    config.sandbox.keep_runtime_alive = False
    return config


@pytest.fixture
def event_stream():
    return EventStream()


def test_memory_limit_enforcement(config, event_stream):
    """Test that memory limits are enforced correctly in the Docker runtime.
    
    This test verifies that:
    1. A process that exceeds a low memory limit gets killed
    2. The same process runs successfully with a higher memory limit
    """
    # Test with low memory limit (128MB)
    config.sandbox.memory_limit = "128m"
    runtime_low_mem = DockerRuntime(config, event_stream, sid='test-low-mem')

    # Connect to initialize the runtime
    runtime_low_mem.connect()

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
    result_low = runtime_low_mem.execute(
        "python",
        input=memory_hog_script,
        timeout=30
    )
    assert result_low.error is not None and \
           ("MemoryError" in result_low.error or "Killed" in result_low.error or result_low.exit_code != 0), \
        "Process should have been killed or raised MemoryError with low memory limit"
    
    # Clean up the low memory runtime
    runtime_low_mem.close()

    # Test with high memory limit (512MB)
    config.sandbox.memory_limit = "512m"
    runtime_high_mem = DockerRuntime(config, event_stream, sid='test-high-mem')

    # Connect to initialize the runtime
    runtime_high_mem.connect()
    
    # Execute with high memory limit - should succeed
    result_high = runtime_high_mem.execute(
        "python",
        input=memory_hog_script,
        timeout=30
    )
    assert result_high.error is None and result_high.exit_code == 0, \
        "Process should have completed successfully with high memory limit"
    assert "Memory allocation successful" in result_high.output, \
        "Process should have completed memory allocation successfully"
    
    # Clean up the high memory runtime
    runtime_high_mem.close()