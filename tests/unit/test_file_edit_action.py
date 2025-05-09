from unittest.mock import MagicMock

from openhands.runtime.action_execution_server import _execute_file_editor


def test_insert_line_string_conversion():
    """Test that insert_line is properly converted from string to int.

    This test reproduces issue #8369 Example 2 where a string value for insert_line
    causes a TypeError in the editor.
    """
    # Mock the OHEditor
    mock_editor = MagicMock()
    mock_editor.return_value = MagicMock(
        error=None, output='Success', old_content=None, new_content=None
    )

    # Test with string insert_line
    result, _ = _execute_file_editor(
        editor=mock_editor,
        command='insert',
        path='/test/path.py',
        insert_line='185',  # String instead of int
        new_str='test content',
    )

    # Verify the editor was called with the correct parameters (insert_line converted to int)
    mock_editor.assert_called_once()
    args, kwargs = mock_editor.call_args
    assert isinstance(kwargs['insert_line'], int)
    assert kwargs['insert_line'] == 185
    assert result == 'Success'
