"""Tests for action execution server idle time updates."""


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

    # Find the specific finally block that contains the update_last_execution_time call
    finally_blocks = server_code.split('finally:')
    found = False
    for block in finally_blocks[
        1:
    ]:  # Skip the first split which is before the first 'finally:'
        if 'update_last_execution_time()' in block:
            found = True
            break

    assert found, 'update_last_execution_time() not found in any finally block'


def test_update_last_execution_time_in_execute_action_endpoint():
    """Test that the update_last_execution_time function is called in the execute_action endpoint."""
    # Read the action_execution_server.py file
    with open(
        '/workspace/OpenHands/openhands/runtime/action_execution_server.py', 'r'
    ) as f:
        server_code = f.read()

    # Find the execute_action endpoint
    execute_action_endpoint = None
    if 'async def execute_action' in server_code:
        execute_action_parts = server_code.split('async def execute_action')
        if len(execute_action_parts) > 1:
            execute_action_endpoint = execute_action_parts[1]

    assert execute_action_endpoint is not None, 'execute_action endpoint not found'

    # Check that the endpoint contains a finally block with update_last_execution_time
    assert 'finally:' in execute_action_endpoint
    assert 'update_last_execution_time()' in execute_action_endpoint

    # Check that update_last_execution_time is called in the finally block
    finally_block = execute_action_endpoint.split('finally:')[1].split('def ')[0]
    assert 'update_last_execution_time()' in finally_block
