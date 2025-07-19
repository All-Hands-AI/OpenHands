"""Unit tests for the Gemini editor tools."""

# Import the consolidated Gemini editing tools from the single module
from openhands.agenthub.codeact_agent.tools.gemini_edit_tools import (
    create_gemini_list_directory_tool,
    create_gemini_read_file_tool,
    create_gemini_replace_tool,
    create_gemini_write_file_tool,
)


def test_create_gemini_read_file_tool_detailed():
    """Test creating the Gemini read_file tool with detailed description."""
    tool = create_gemini_read_file_tool(detailed=True)

    assert tool['type'] == 'function'
    assert tool['function']['name'] == 'read_file'
    assert 'Reads and returns the content' in tool['function']['description']
    assert 'text files' in tool['function']['description']
    assert 'line ranges' in tool['function']['description']

    # Check parameters
    params = tool['function']['parameters']
    assert params['type'] == 'object'
    assert 'absolute_path' in params['properties']
    assert 'offset' in params['properties']
    assert 'limit' in params['properties']

    # Check required parameters
    assert params['required'] == ['absolute_path']

    # Check parameter types
    assert params['properties']['absolute_path']['type'] == 'string'
    assert params['properties']['offset']['type'] == 'number'
    assert params['properties']['limit']['type'] == 'number'


def test_create_gemini_write_file_tool_short():
    """Test creating the Gemini write_file tool with short description."""
    tool = create_gemini_write_file_tool(detailed=False)

    assert tool['type'] == 'function'
    assert tool['function']['name'] == 'write_file'
    assert 'Write content to a file' in tool['function']['description']

    # Short description should be shorter than detailed
    detailed_tool = create_gemini_write_file_tool(detailed=True)
    assert len(tool['function']['description']) < len(
        detailed_tool['function']['description']
    )


def test_gemini_replace_tool_parameter_types():
    """Test that the Gemini replace tool has correct parameter types."""
    tool = create_gemini_replace_tool()
    params = tool['function']['parameters']['properties']

    # Check string parameters
    string_params = ['file_path', 'old_string', 'new_string']
    for param in string_params:
        assert params[param]['type'] == 'string'

    # Check number parameters (Gemini CLI uses 'number' not 'integer')
    assert params['expected_replacements']['type'] == 'number'
    assert params['expected_replacements']['minimum'] == 1

    # Check required parameters
    assert tool['function']['parameters']['required'] == [
        'file_path',
        'old_string',
        'new_string',
    ]


def test_gemini_list_directory_tool_parameter_types():
    """Test that the Gemini list_directory tool has correct parameter types."""
    tool = create_gemini_list_directory_tool()
    params = tool['function']['parameters']['properties']

    # Check string parameter
    assert params['path']['type'] == 'string'

    # Check array parameter
    assert params['ignore']['type'] == 'array'
    assert params['ignore']['items']['type'] == 'string'

    # Check boolean parameter
    assert params['respect_git_ignore']['type'] == 'boolean'

    # Check required parameters
    assert tool['function']['parameters']['required'] == ['path']
