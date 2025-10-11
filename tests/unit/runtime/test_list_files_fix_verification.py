"""Direct verification test that proves our fix works.

This test directly verifies that the actual list_files method code
correctly includes the recursive parameter.
"""

import inspect
from unittest.mock import Mock

from openhands.runtime.impl.action_execution.action_execution_client import (
    ActionExecutionClient,
)


def test_actual_source_code_has_the_fix():
    """Verify the actual source code contains our fix."""
    # Get the actual source code of the list_files method
    source_code = inspect.getsource(ActionExecutionClient.list_files)

    # Verify the fix is in the actual source code
    assert "data['recursive'] = recursive" in source_code, (
        "The fix 'data['recursive'] = recursive' is not in the source code!"
    )

    # Verify the OLD buggy code is NOT there
    assert "if recursive:" not in source_code or "if recursive:" not in source_code.split("data['recursive']")[0], (
        "The old buggy 'if recursive:' condition is still there!"
    )

    print("✓ Verified: Source code contains the fix: data['recursive'] = recursive")


def test_list_files_method_builds_correct_data():
    """Test the actual list_files method logic by executing it."""
    # Create a minimal mock that has just what list_files needs
    mock_client = Mock()
    mock_client.log = Mock()
    mock_client.action_execution_server_url = 'http://test'

    # Track what data gets passed to _send_action_server_request
    captured_data = {}

    def capture_json_data(*args, **kwargs):
        captured_data['json'] = kwargs.get('json')
        mock_response = Mock()
        mock_response.json.return_value = []
        mock_response.is_closed = True
        return mock_response

    mock_client._send_action_server_request = capture_json_data

    # Now call the REAL list_files method with the mock client
    # This executes the actual method code, including our fix
    result = ActionExecutionClient.list_files(mock_client, path='/test', recursive=False)

    # Verify that recursive=False was included in the data
    assert captured_data['json'] == {'path': '/test', 'recursive': False}, (
        f"Expected recursive=False in data, got: {captured_data['json']}"
    )
    print("✓ Test 1: Verified recursive=False is sent")

    # Test with recursive=True
    captured_data.clear()
    result = ActionExecutionClient.list_files(mock_client, path='/test', recursive=True)
    assert captured_data['json'] == {'path': '/test', 'recursive': True}
    print("✓ Test 2: Verified recursive=True is sent")

    # Test with default (should be False)
    captured_data.clear()
    result = ActionExecutionClient.list_files(mock_client, path='/test')
    assert captured_data['json'] == {'path': '/test', 'recursive': False}
    print("✓ Test 3: Verified default recursive=False is sent")


def test_demonstrate_old_bug_vs_new_fix():
    """Demonstrate what the old bug was and how the fix solves it."""
    print("\n=== Demonstrating the Bug and Fix ===")

    # OLD BUGGY CODE (what it used to do)
    def old_buggy_list_files(recursive=False):
        data = {}
        if recursive:  # This would skip when recursive=False!
            data['recursive'] = recursive
        return data

    # NEW FIXED CODE (what it does now)
    def new_fixed_list_files(recursive=False):
        data = {}
        data['recursive'] = recursive  # Always include it!
        return data

    # Show the bug
    old_result = old_buggy_list_files(recursive=False)
    assert old_result == {}, "Old code would send empty dict!"
    print(f"✗ OLD BUGGY CODE with recursive=False: {old_result} (missing recursive!)")

    old_result = old_buggy_list_files(recursive=True)
    assert old_result == {'recursive': True}
    print(f"✓ OLD CODE with recursive=True: {old_result} (worked)")

    # Show the fix
    new_result = new_fixed_list_files(recursive=False)
    assert new_result == {'recursive': False}
    print(f"✓ NEW FIXED CODE with recursive=False: {new_result} (includes recursive!)")

    new_result = new_fixed_list_files(recursive=True)
    assert new_result == {'recursive': True}
    print(f"✓ NEW FIXED CODE with recursive=True: {new_result} (still works)")

    print("\nThe fix ensures 'recursive' is ALWAYS sent, even when False!")


if __name__ == "__main__":
    test_actual_source_code_has_the_fix()
    test_list_files_method_builds_correct_data()
    test_demonstrate_old_bug_vs_new_fix()
    print("\n✅ ALL TESTS PASSED - The fix is real and working!")