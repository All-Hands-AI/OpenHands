"""Test for the Gemini read_file action to reproduce and fix the path issue."""

import os
import tempfile

from litellm import ModelResponse

from openhands.agenthub.codeact_agent.function_calling import response_to_actions
from openhands.agenthub.codeact_agent.tools.gemini_edit_tools import (
    create_gemini_read_file_tool,
)
from openhands.events.action import FileReadAction
from openhands.events.event import FileReadSource


def create_mock_response(tool_name, arguments):
    """Create a properly structured ModelResponse for testing."""
    # Create a simple dictionary structure that matches what ModelResponse expects
    response_dict = {
        'id': 'test-response-id',
        'choices': [
            {
                'index': 0,
                'message': {
                    'content': 'Reading file',
                    'role': 'assistant',
                    'tool_calls': [
                        {
                            'id': 'test-tool-call-id',
                            'type': 'function',
                            'function': {'name': tool_name, 'arguments': arguments},
                        }
                    ],
                },
            }
        ],
        'model': 'test-model',
        'object': 'chat.completion',
    }

    # Convert the dictionary to a ModelResponse object
    return ModelResponse(**response_dict)


def test_gemini_read_file_action_path_validation():
    """Test that the read_file action correctly handles paths."""
    # Create a temporary file for testing
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file.write(b'Test content')
        temp_path = temp_file.name

    try:
        # Test with absolute path (should work)
        response = create_mock_response(
            'read_file', f'{{"absolute_path": "{temp_path}"}}'
        )

        actions = response_to_actions(response)
        assert len(actions) == 1
        assert isinstance(actions[0], FileReadAction)
        assert actions[0].path == temp_path
        assert actions[0].impl_source == FileReadSource.OH_ACI

        # Test with non-absolute path (should still work at this level)
        # The actual validation happens at runtime in the OHEditor.read_file method
        relative_path = 'docs/README.md'
        response = create_mock_response(
            'read_file', f'{{"absolute_path": "{relative_path}"}}'
        )

        actions = response_to_actions(response)
        assert len(actions) == 1
        assert isinstance(actions[0], FileReadAction)
        assert actions[0].path == relative_path
        assert actions[0].impl_source == FileReadSource.OH_ACI

    finally:
        # Clean up the temporary file
        os.unlink(temp_path)


def test_gemini_read_file_tool_path_pattern():
    """Test that the read_file tool enforces absolute paths in its schema."""
    tool = create_gemini_read_file_tool()

    # Check that the absolute_path parameter has a pattern that enforces absolute paths
    # Note: We're using dictionary access here because the ChatCompletionToolParam class
    # has a __getitem__ method that allows it to be accessed like a dictionary
    params = tool['function']['parameters']['properties']
    assert 'absolute_path' in params
    assert 'pattern' in params['absolute_path']
    assert params['absolute_path']['pattern'] == '^/'
