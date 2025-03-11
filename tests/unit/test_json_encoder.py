import gc
from datetime import datetime

import psutil

from openhands.io.json import dumps


def get_memory_usage():
    """Get current memory usage of the process"""
    process = psutil.Process()
    return process.memory_info().rss


def test_json_encoder_memory_leak():
    # Force garbage collection before test
    gc.collect()
    initial_memory = get_memory_usage()

    # Create a large dataset that will need encoding
    large_data = {
        'datetime': datetime.now(),
        'nested': [{'timestamp': datetime.now()} for _ in range(1000)],
    }

    # Track memory usage over multiple iterations
    memory_samples = []
    for i in range(10):
        # Perform multiple serializations in each iteration
        for _ in range(100):
            dumps(large_data)
            dumps(large_data, indent=2)  # Test with kwargs too

        # Force garbage collection
        gc.collect()
        memory_samples.append(get_memory_usage())

    # Check if memory usage is stable (not continuously growing)
    # We expect some fluctuation but not a steady increase
    max_memory = max(memory_samples)
    min_memory = min(memory_samples)
    memory_variation = max_memory - min_memory

    # Allow for some memory variation (2MB) due to Python's memory management
    assert (
        memory_variation < 2 * 1024 * 1024
    ), f'Memory usage unstable: {memory_variation} bytes variation'

    # Also check total memory increase from start
    final_memory = memory_samples[-1]
    memory_increase = final_memory - initial_memory

    # Allow for some memory increase (2MB) as some objects may be cached
    assert (
        memory_increase < 2 * 1024 * 1024
    ), f'Memory leak detected: {memory_increase} bytes increase'
