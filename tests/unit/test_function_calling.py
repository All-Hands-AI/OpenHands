"""Test function calling module."""

import json
from unittest.mock import patch

import pytest
from litellm import ModelResponse

from openhands.agenthub.codeact_agent.function_calling import (
    get_tools,
    response_to_actions,
)
from openhands.agenthub.codeact_agent.tools import (
    BrowserTool,
    FencedDiffEditTool,
    FinishTool,
    IPythonTool,
    ListDirectoryTool,
    LLMBasedFileEditTool,
    ThinkTool,
    UndoEditTool,
    ViewFileTool,
    WebReadTool,
    create_cmd_run_tool,
    create_str_replace_editor_tool,
)
from openhands.core.config import AgentConfig
from openhands.core.exceptions import FunctionCallValidationError
from openhands.events.action import (
    AgentThinkAction,
    BrowseInteractiveAction,
    CmdRunAction,
    FileEditAction,
    FileReadAction,
    IPythonRunCellAction,
    MessageAction,
)
from openhands.events.event import FileEditSource, FileReadSource


# Helper to create AgentConfig with specific flags
def create_test_config(**kwargs) -> AgentConfig:
    defaults = {
        'enable_browsing': False,
        'enable_llm_editor': False,
        'enable_llm_diff': False,
        'enable_jupyter': False,
        # Add other AgentConfig defaults if necessary for validation
        'disabled_microagents': [],
        'enable_prompt_extensions': True,
        'enable_history_truncation': True,
        'enable_som_visual_browsing': True,
    }
    defaults.update(kwargs)
    # Use model_validate to ensure proper Pydantic model creation
    return AgentConfig.model_validate(defaults)


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
        # Add dummy usage if needed by downstream processing
        usage={'prompt_tokens': 10, 'completion_tokens': 10, 'total_tokens': 20},
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
    """Test edit_file with valid arguments (LLMBasedFileEditTool)."""
    # This tests the LLMBasedFileEditTool specifically
    response = create_mock_response(
        LLMBasedFileEditTool['function']['name'],  # Use tool name
        {'path': '/path/to/file', 'content': 'file content', 'start': 1, 'end': 10},
    )
    actions = response_to_actions(response)
    assert len(actions) == 1
    assert isinstance(actions[0], FileEditAction)
    assert actions[0].path == '/path/to/file'
    assert actions[0].content == 'file content'
    assert actions[0].start == 1
    assert actions[0].end == 10
    assert (
        actions[0].impl_source == FileEditSource.LLM_BASED_EDIT
    )  # Default when tool called


def test_edit_file_missing_required():
    """Test edit_file with missing required arguments (LLMBasedFileEditTool)."""
    # Missing path
    response = create_mock_response(
        LLMBasedFileEditTool['function']['name'], {'content': 'content'}
    )
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

    # Test other commands (e.g., replace)
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
    response = create_mock_response(
        BrowserTool['function']['name'], {'code': "click('button-1')"}
    )
    actions = response_to_actions(response)
    assert len(actions) == 1
    assert isinstance(actions[0], BrowseInteractiveAction)
    assert actions[0].browser_actions == "click('button-1')"


def test_browser_missing_code():
    """Test browser with missing code argument."""
    response = create_mock_response(BrowserTool['function']['name'], {})
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
        usage={'prompt_tokens': 10, 'completion_tokens': 10, 'total_tokens': 20},
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


# =============================================
# Tests for get_tools based on AgentConfig
# =============================================


def test_get_tools_default():
    """Test default tools when no specific editor is enabled."""
    config = create_test_config()
    tools = get_tools(config)
    tool_names = {t['function']['name'] for t in tools}
    assert create_str_replace_editor_tool()['function']['name'] in tool_names
    assert FencedDiffEditTool['function']['name'] not in tool_names
    assert LLMBasedFileEditTool['function']['name'] not in tool_names
    assert ViewFileTool['function']['name'] not in tool_names  # Included in str_replace
    assert (
        ListDirectoryTool['function']['name'] not in tool_names
    )  # Included in str_replace
    assert UndoEditTool['function']['name'] not in tool_names  # Included in str_replace


def test_get_tools_llm_diff_enabled():
    """Test tools when LLM Diff mode is enabled."""
    config = create_test_config(
        enable_llm_diff=True,
        enable_browsing=True,
        enable_jupyter=True,
    )
    tools = get_tools(config)
    tool_names = {t['function']['name'] for t in tools}

    # Should include non-edit tools
    assert create_cmd_run_tool()['function']['name'] in tool_names
    assert ThinkTool['function']['name'] in tool_names
    assert FinishTool['function']['name'] in tool_names
    assert WebReadTool['function']['name'] in tool_names
    assert BrowserTool['function']['name'] in tool_names
    assert IPythonTool['function']['name'] in tool_names
    assert ViewFileTool['function']['name'] in tool_names
    assert ListDirectoryTool['function']['name'] in tool_names

    # Should NOT include edit tools or Undo
    assert create_str_replace_editor_tool()['function']['name'] not in tool_names
    assert FencedDiffEditTool['function']['name'] not in tool_names
    assert LLMBasedFileEditTool['function']['name'] not in tool_names
    assert UndoEditTool['function']['name'] not in tool_names


def test_get_tools_llm_editor_enabled():
    """Test tools when LLM Editor tool is enabled."""
    config = create_test_config(enable_llm_editor=True)
    tools = get_tools(config)
    tool_names = {t['function']['name'] for t in tools}
    assert LLMBasedFileEditTool['function']['name'] in tool_names
    assert ViewFileTool['function']['name'] in tool_names
    assert ListDirectoryTool['function']['name'] in tool_names
    assert UndoEditTool['function']['name'] not in tool_names  # Undo not compatible
    assert create_str_replace_editor_tool()['function']['name'] not in tool_names
    assert FencedDiffEditTool['function']['name'] not in tool_names


# =============================================
# Tests for response_to_actions with LLM_DIFF
# =============================================


# Mock ModelResponse without tool calls, but with content
def create_mock_response_no_tools(content: str) -> ModelResponse:
    """Helper function to create a mock response without tool calls."""
    return ModelResponse(
        id='mock-no-tools-id',
        choices=[
            {
                'message': {
                    'tool_calls': None,  # Explicitly None
                    'content': content,
                    'role': 'assistant',
                },
                'index': 0,
                'finish_reason': 'stop',  # Or other non-tool reason
            }
        ],
        # Add dummy usage if needed by downstream processing
        usage={'prompt_tokens': 10, 'completion_tokens': 10, 'total_tokens': 20},
    )


def test_response_to_actions_llm_diff_mode_with_blocks():
    """Test parsing diff blocks when llm_diff is enabled and no tool calls."""
    content = """
Thinking about the changes...
```python
file.py
<<<<<<< SEARCH
old line
=======
new line
>>>>>>> REPLACE
```
Another block:
```python
file.py
<<<<<<< SEARCH
second old
=======
second new
>>>>>>> REPLACE
```
"""
    response = create_mock_response_no_tools(content)
    actions = response_to_actions(response, is_llm_diff_enabled=True)  # Enable flag

    assert len(actions) == 3  # Think + 2 Edits
    assert isinstance(actions[0], AgentThinkAction)
    assert actions[0].thought == 'Thinking about the changes...'

    assert isinstance(actions[1], FileEditAction)
    assert actions[1].path == 'file.py'
    assert actions[1].search == 'old line\n'
    assert actions[1].replace == 'new line\n'
    assert actions[1].impl_source == FileEditSource.LLM_DIFF

    assert isinstance(actions[2], FileEditAction)
    assert actions[2].path == 'file.py'
    assert actions[2].search == 'second old\n'
    assert actions[2].replace == 'second new\n'
    assert actions[2].impl_source == FileEditSource.LLM_DIFF


def test_response_to_actions_llm_diff_mode_no_blocks():
    """Test llm_diff mode when response content has no blocks."""
    content = 'Just a simple message.'
    response = create_mock_response_no_tools(content)
    actions = response_to_actions(response, is_llm_diff_enabled=True)  # Enable flag

    assert len(actions) == 1
    assert isinstance(actions[0], MessageAction)
    assert actions[0].content == content


def test_response_to_actions_llm_diff_mode_parse_error(mocker):
    """Test llm_diff mode when parsing fails."""
    content = """
```python
file.py
<<<<<<< SEARCH
old
# Malformed block - missing divider
new
>>>>>>> REPLACE
```
"""
    response = create_mock_response_no_tools(content)
    # Mock the parser to raise ValueError
    mocker.patch(
        'openhands.agenthub.codeact_agent.function_calling.parse_llm_response_for_diffs',
        side_effect=ValueError('Test parse error'),
    )

    actions = response_to_actions(response, is_llm_diff_enabled=True)  # Enable flag

    assert len(actions) == 1
    assert isinstance(actions[0], MessageAction)
    assert 'Error parsing diff blocks: Test parse error' in actions[0].content


def test_response_to_actions_llm_diff_mode_with_tool_calls():
    """Test llm_diff mode is ignored if tool calls are present."""
    # Create a response that HAS tool calls, even though llm_diff is enabled
    response = create_mock_response('execute_bash', {'command': 'echo hello'})
    # Add some content that looks like a diff block, to ensure it's ignored
    response.choices[0]['message']['content'] = """
```python
file.py
<<<<<<< SEARCH
ignored old
=======
ignored new
>>>>>>> REPLACE
```
"""

    actions = response_to_actions(response, is_llm_diff_enabled=True)
    assert len(actions) == 1
    assert isinstance(actions[0], CmdRunAction)
    assert actions[0].command == 'echo hello'


def test_response_to_actions_llm_diff_mode_multiple_errors():
    """Test handling of multiple errors in diff blocks."""
    content = """
```python
file1.py
<<<<<<< SEARCH
old content
# Missing divider
new content
>>>>>>> REPLACE
```
```python
# Missing filename
<<<<<<< SEARCH
more old content
=======
more new content
>>>>>>> REPLACE
```
"""
    response = create_mock_response_no_tools(content)
    actions = response_to_actions(response, is_llm_diff_enabled=True)

    assert len(actions) == 1
    assert isinstance(actions[0], MessageAction)
    assert 'Error parsing block #1' in actions[0].content
    assert 'Expected `=======`' in actions[0].content


def test_response_to_actions_llm_diff_mode_whitespace_edge_cases():
    """Test handling of whitespace edge cases in diff blocks."""
    content = """
```python
file.py
<<<<<<< SEARCH

    indented line
trailing space
=======

    new indented line
new trailing space
>>>>>>> REPLACE
```
"""
    response = create_mock_response_no_tools(content)
    actions = response_to_actions(response, is_llm_diff_enabled=True)

    assert len(actions) == 1
    assert isinstance(actions[0], FileEditAction)
    assert actions[0].path == 'file.py'
    assert actions[0].search == '\n    indented line\ntrailing space   \n'
    assert actions[0].replace == '\n    new indented line\nnew trailing space   \n'


def test_response_to_actions_llm_diff_mode_empty_lines():
    """Test handling of empty lines in diff blocks."""
    content = """
```python
file.py
<<<<<<< SEARCH


=======


>>>>>>> REPLACE
```
"""
    response = create_mock_response_no_tools(content)
    actions = response_to_actions(response, is_llm_diff_enabled=True)

    assert len(actions) == 1
    assert isinstance(actions[0], FileEditAction)
    assert actions[0].path == 'file.py'
    assert actions[0].search == '\n\n\n'
    assert actions[0].replace == '\n\n\n'

    # Should process the tool call, not the diff block
    assert len(actions) == 1
    assert isinstance(actions[0], CmdRunAction)
    assert actions[0].command == 'echo hello'
    # Check that the thought includes the content that was ignored for parsing
    assert 'ignored old' in actions[0].thought


def test_response_to_actions_llm_diff_disabled_no_tools():
    """Test response parsing when llm_diff is disabled and no tool calls."""
    content = """
Thinking about the changes...
```python
file.py
<<<<<<< SEARCH
old line
=======
new line
>>>>>>> REPLACE
```
"""
    response = create_mock_response_no_tools(content)
    actions = response_to_actions(
        response, is_llm_diff_enabled=False
    )  # Explicitly disable

    # Should just be a MessageAction, no parsing attempted
    assert len(actions) == 1
    assert isinstance(actions[0], MessageAction)
    assert actions[0].content == content
