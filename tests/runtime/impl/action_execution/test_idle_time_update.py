"""Tests for idle time updates in action execution."""

import time

from openhands.runtime.utils.system_stats import (
    get_system_info,
    update_last_execution_time,
)


def test_update_last_execution_time_resets_idle_time():
    """Test that update_last_execution_time resets the idle time."""
    # Get initial system info
    initial_info = get_system_info()
    initial_idle_time = initial_info['idle_time']

    # Wait a bit
    time.sleep(0.2)

    # Update last execution time
    update_last_execution_time()

    # Get updated system info
    updated_info = get_system_info()
    updated_idle_time = updated_info['idle_time']

    # The idle time should have been reset
    assert updated_idle_time < initial_idle_time
    assert updated_idle_time < 0.1  # Should be very small


def test_action_execution_client_has_update_call():
    """Test that the action execution client code includes calls to update_last_execution_time."""
    # Read the action_execution_client.py file
    with open(
        '/workspace/OpenHands/openhands/runtime/impl/action_execution/action_execution_client.py',
        'r',
    ) as f:
        client_code = f.read()

    # Check that the file contains the update_last_execution_time call
    assert 'update_last_execution_time()' in client_code

    # Check that it's in a finally block
    assert 'finally:' in client_code

    # Find the specific finally block that contains the update_last_execution_time call
    finally_blocks = client_code.split('finally:')
    found = False
    for block in finally_blocks[
        1:
    ]:  # Skip the first split which is before the first 'finally:'
        if 'update_last_execution_time()' in block:
            found = True
            break

    assert found, 'update_last_execution_time() not found in any finally block'


def test_action_execution_server_has_update_call():
    """Test that the action execution server code includes calls to update_last_execution_time."""
    # Read the action_execution_server.py file
    with open(
        '/workspace/OpenHands/openhands/runtime/action_execution_server.py', 'r'
    ) as f:
        server_code = f.read()

    # Check that the file contains the update_last_execution_time call
    assert 'update_last_execution_time()' in server_code

    # Check that it's in a finally block
    assert 'finally:' in server_code
    assert 'update_last_execution_time()' in server_code.split('finally:')[1]
