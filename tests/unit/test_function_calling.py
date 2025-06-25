"""Test function calling module."""

import json
from unittest.mock import patch

import pytest
from litellm import ModelResponse

from openhands.agenthub.codeact_agent.function_calling import response_to_actions
from openhands.core.exceptions import FunctionCallValidationError
from openhands.events.action import (
    BrowseInteractiveAction,
    CmdRunAction,
    FileEditAction,
    FileReadAction,
    IPythonRunCellAction,
)
from openhands.events.event import FileEditSource, FileReadSource


def create_mock_response(function_name: str, arguments: dict) -> ModelResponse:
    """Helper function to create a mock response with a tool call."""
    return ModelResponse(
        id='mock-id',
        choices=[
            {
                'message': {
                    'tool_calls': [
                        {
                            'function': {
                                'name': function_name,
                                'arguments': json.dumps(arguments),
                            },
                            'id': 'mock-tool-call-id',
                            'type': 'function',
                        }
                    ],
                    'content': None,
                    'role': 'assistant',
                },
                'index': 0,
                'finish_reason': 'tool_calls',
            }
        ],
    )


def test_execute_bash_valid():
    """Test execute_bash with valid arguments."""
    response = create_mock_response(
        'execute_bash', {'command': 'ls', 'is_input': 'false'}
    )
    actions = response_to_actions(response)
    assert len(actions) == 1
    assert isinstance(actions[0], CmdRunAction)
    assert actions[0].command == 'ls'
    assert actions[0].is_input is False

    # Test with timeout parameter
    with patch.object(CmdRunAction, 'set_hard_timeout') as mock_set_hard_timeout:
        response_with_timeout = create_mock_response(
            'execute_bash', {'command': 'ls', 'is_input': 'false', 'timeout': 30}
        )
        actions_with_timeout = response_to_actions(response_with_timeout)

        # Verify set_hard_timeout was called with the correct value
        mock_set_hard_timeout.assert_called_once_with(30.0)

        assert len(actions_with_timeout) == 1
        assert isinstance(actions_with_timeout[0], CmdRunAction)
        assert actions_with_timeout[0].command == 'ls'
        assert actions_with_timeout[0].is_input is False


def test_execute_bash_missing_command():
    """Test execute_bash with missing command argument."""
    response = create_mock_response('execute_bash', {'is_input': 'false'})
    with pytest.raises(FunctionCallValidationError) as exc_info:
        response_to_actions(response)
    assert 'Missing required argument "command"' in str(exc_info.value)


def test_execute_ipython_cell_valid():
    """Test execute_ipython_cell with valid arguments."""
    response = create_mock_response('execute_ipython_cell', {'code': "print('hello')"})
    actions = response_to_actions(response)
    assert len(actions) == 1
    assert isinstance(actions[0], IPythonRunCellAction)
    assert actions[0].code == "print('hello')"


def test_execute_ipython_cell_missing_code():
    """Test execute_ipython_cell with missing code argument."""
    response = create_mock_response('execute_ipython_cell', {})
    with pytest.raises(FunctionCallValidationError) as exc_info:
        response_to_actions(response)
    assert 'Missing required argument "code"' in str(exc_info.value)


def test_edit_file_valid():
    """Test edit_file with valid arguments."""
    response = create_mock_response(
        'edit_file',
        {'path': '/path/to/file', 'content': 'file content', 'start': 1, 'end': 10},
    )
    actions = response_to_actions(response)
    assert len(actions) == 1
    assert isinstance(actions[0], FileEditAction)
    assert actions[0].path == '/path/to/file'
    assert actions[0].content == 'file content'
    assert actions[0].start == 1
    assert actions[0].end == 10


def test_edit_file_missing_required():
    """Test edit_file with missing required arguments."""
    # Missing path
    response = create_mock_response('edit_file', {'content': 'content'})
    with pytest.raises(FunctionCallValidationError) as exc_info:
        response_to_actions(response)
    assert 'Missing required argument "path"' in str(exc_info.value)

    # Missing content
    response = create_mock_response('edit_file', {'path': '/path/to/file'})
    with pytest.raises(FunctionCallValidationError) as exc_info:
        response_to_actions(response)
    assert 'Missing required argument "content"' in str(exc_info.value)


def test_str_replace_editor_valid():
    """Test str_replace_editor with valid arguments."""
    # Test view command
    response = create_mock_response(
        'str_replace_editor', {'command': 'view', 'path': '/path/to/file'}
    )
    actions = response_to_actions(response)
    assert len(actions) == 1
    assert isinstance(actions[0], FileReadAction)
    assert actions[0].path == '/path/to/file'
    assert actions[0].impl_source == FileReadSource.OH_ACI

    # Test other commands
    response = create_mock_response(
        'str_replace_editor',
        {
            'command': 'str_replace',
            'path': '/path/to/file',
            'old_str': 'old',
            'new_str': 'new',
        },
    )
    actions = response_to_actions(response)
    assert len(actions) == 1
    assert isinstance(actions[0], FileEditAction)
    assert actions[0].path == '/path/to/file'
    assert actions[0].impl_source == FileEditSource.OH_ACI


def test_str_replace_editor_missing_required():
    """Test str_replace_editor with missing required arguments."""
    # Missing command
    response = create_mock_response('str_replace_editor', {'path': '/path/to/file'})
    with pytest.raises(FunctionCallValidationError) as exc_info:
        response_to_actions(response)
    assert 'Missing required argument "command"' in str(exc_info.value)

    # Missing path
    response = create_mock_response('str_replace_editor', {'command': 'view'})
    with pytest.raises(FunctionCallValidationError) as exc_info:
        response_to_actions(response)
    assert 'Missing required argument "path"' in str(exc_info.value)


def test_browser_valid():
    """Test browser with valid arguments."""
    response = create_mock_response('browser', {'code': "click('button-1')"})
    actions = response_to_actions(response)
    assert len(actions) == 1
    assert isinstance(actions[0], BrowseInteractiveAction)
    assert actions[0].browser_actions == "click('button-1')"
    assert actions[0].return_axtree is False  # Default value should be False


def test_browser_missing_code():
    """Test browser with missing code argument."""
    response = create_mock_response('browser', {})
    with pytest.raises(FunctionCallValidationError) as exc_info:
        response_to_actions(response)
    assert 'Missing required argument "code"' in str(exc_info.value)


def test_invalid_json_arguments():
    """Test handling of invalid JSON in arguments."""
    response = ModelResponse(
        id='mock-id',
        choices=[
            {
                'message': {
                    'tool_calls': [
                        {
                            'function': {
                                'name': 'execute_bash',
                                'arguments': 'invalid json',
                            },
                            'id': 'mock-tool-call-id',
                            'type': 'function',
                        }
                    ],
                    'content': None,
                    'role': 'assistant',
                },
                'index': 0,
                'finish_reason': 'tool_calls',
            }
        ],
    )
    with pytest.raises(FunctionCallValidationError) as exc_info:
        response_to_actions(response)
    assert 'Failed to parse tool call arguments' in str(exc_info.value)


def test_unexpected_argument_handling():
    """Test that unexpected arguments in function calls are properly handled.

    This test reproduces issue #8369 Example 4 where an unexpected argument
    (old_str_prefix) causes a TypeError.
    """
    response = create_mock_response(
        'str_replace_editor',
        {
            'command': 'str_replace',
            'path': '/test/file.py',
            'old_str': 'def test():\n    pass',
            'new_str': 'def test():\n    return True',
            'old_str_prefix': 'some prefix',  # Unexpected argument
        },
    )

    # Test that the function raises a FunctionCallValidationError
    with pytest.raises(FunctionCallValidationError) as exc_info:
        response_to_actions(response)

    # Verify the error message mentions the unexpected argument
    assert 'old_str_prefix' in str(exc_info.value)
    assert 'Unexpected argument' in str(exc_info.value)


def test_str_replace_editor_create_missing_file_text():
    """Test that str_replace_editor create command fails when file_text is missing."""
    response = create_mock_response(
        'str_replace_editor',
        {
            'command': 'create',
            'path': '/test/file.py',
            # Missing file_text parameter
        },
    )

    with pytest.raises(FunctionCallValidationError) as exc_info:
        response_to_actions(response)

    assert 'Missing required argument "file_text" for command "create"' in str(
        exc_info.value
    )


def test_str_replace_editor_create_with_file_text():
    """Test that str_replace_editor create command works when file_text is provided."""
    response = create_mock_response(
        'str_replace_editor',
        {
            'command': 'create',
            'path': '/test/file.py',
            'file_text': 'print("Hello, World!")',
        },
    )

    actions = response_to_actions(response)
    assert len(actions) == 1
    action = actions[0]
    assert isinstance(action, FileEditAction)
    assert action.path == '/test/file.py'
    assert action.command == 'create'
    assert action.file_text == 'print("Hello, World!")'


def test_str_replace_editor_str_replace_missing_old_str():
    """Test that str_replace_editor str_replace command fails when old_str is missing."""
    response = create_mock_response(
        'str_replace_editor',
        {
            'command': 'str_replace',
            'path': '/test/file.py',
            'new_str': 'new content',
            # Missing old_str parameter
        },
    )

    with pytest.raises(FunctionCallValidationError) as exc_info:
        response_to_actions(response)

    assert 'Missing required argument "old_str" for command "str_replace"' in str(
        exc_info.value
    )


def test_str_replace_editor_str_replace_missing_new_str():
    """Test that str_replace_editor str_replace command fails when new_str is missing."""
    response = create_mock_response(
        'str_replace_editor',
        {
            'command': 'str_replace',
            'path': '/test/file.py',
            'old_str': 'old content',
            # Missing new_str parameter
        },
    )

    with pytest.raises(FunctionCallValidationError) as exc_info:
        response_to_actions(response)

    assert 'Missing required argument "new_str" for command "str_replace"' in str(
        exc_info.value
    )


def test_str_replace_editor_insert_missing_new_str():
    """Test that str_replace_editor insert command fails when new_str is missing."""
    response = create_mock_response(
        'str_replace_editor',
        {
            'command': 'insert',
            'path': '/test/file.py',
            'insert_line': 5,
            # Missing new_str parameter
        },
    )

    with pytest.raises(FunctionCallValidationError) as exc_info:
        response_to_actions(response)

    assert 'Missing required argument "new_str" for command "insert"' in str(
        exc_info.value
    )


def test_str_replace_editor_insert_missing_insert_line():
    """Test that str_replace_editor insert command fails when insert_line is missing."""
    response = create_mock_response(
        'str_replace_editor',
        {
            'command': 'insert',
            'path': '/test/file.py',
            'new_str': 'new content',
            # Missing insert_line parameter
        },
    )

    with pytest.raises(FunctionCallValidationError) as exc_info:
        response_to_actions(response)

    assert 'Missing required argument "insert_line" for command "insert"' in str(
        exc_info.value
    )


def test_str_replace_editor_insert_with_all_params():
    """Test that str_replace_editor insert command works when all parameters are provided."""
    response = create_mock_response(
        'str_replace_editor',
        {
            'command': 'insert',
            'path': '/test/file.py',
            'new_str': 'new content',
            'insert_line': 5,
        },
    )

    actions = response_to_actions(response)
    assert len(actions) == 1
    action = actions[0]
    assert isinstance(action, FileEditAction)
    assert action.path == '/test/file.py'
    assert action.command == 'insert'
    assert action.new_str == 'new content'
    assert action.insert_line == 5
