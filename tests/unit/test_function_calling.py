"""Test function calling module."""

import json

import pytest
from litellm import ModelResponse

from openhands.agenthub.codeact_agent.function_calling import response_to_actions
from openhands.core.exceptions import FunctionCallValidationError
from openhands.events.action import (
    BrowseInteractiveAction,
    BrowseURLAction,
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


def test_browser_missing_code():
    """Test browser with missing code argument."""
    response = create_mock_response('browser', {})
    with pytest.raises(FunctionCallValidationError) as exc_info:
        response_to_actions(response)
    assert 'Missing required argument "code"' in str(exc_info.value)


def test_web_read_valid():
    """Test web_read with valid arguments."""
    response = create_mock_response('web_read', {'url': 'https://example.com'})
    actions = response_to_actions(response)
    assert len(actions) == 1
    assert isinstance(actions[0], BrowseURLAction)
    assert actions[0].url == 'https://example.com'


def test_web_read_missing_url():
    """Test web_read with missing url argument."""
    response = create_mock_response('web_read', {})
    with pytest.raises(FunctionCallValidationError) as exc_info:
        response_to_actions(response)
    assert 'Missing required argument "url"' in str(exc_info.value)


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
    with pytest.raises(RuntimeError) as exc_info:
        response_to_actions(response)
    assert 'Failed to parse tool call arguments' in str(exc_info.value)
