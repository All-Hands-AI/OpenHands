"""Unit tests for the Gemini editor tool."""

from openhands.agenthub.codeact_agent.tools.gemini_editor import (
    create_gemini_editor_tool,
)
from openhands.llm.tool_names import GEMINI_EDITOR_TOOL_NAME


def test_create_gemini_editor_tool_detailed():
    """Test creating the Gemini editor tool with detailed description."""
    tool = create_gemini_editor_tool(use_short_description=False)

    assert tool['type'] == 'function'
    assert tool['function']['name'] == GEMINI_EDITOR_TOOL_NAME
    assert 'Gemini-style editing tool' in tool['function']['description']
    assert 'replace' in tool['function']['description']
    assert 'write_file' in tool['function']['description']
    assert 'read_file' in tool['function']['description']
    assert 'list_directory' in tool['function']['description']

    # Check parameters (updated for Gemini CLI alignment)
    params = tool['function']['parameters']
    assert params['type'] == 'object'
    assert 'command' in params['properties']

    # Check Gemini CLI-aligned parameters
    assert 'absolute_path' in params['properties']  # read_file parameter
    assert 'file_path' in params['properties']  # write_file and replace parameter
    assert 'path' in params['properties']  # list_directory parameter
    assert 'old_string' in params['properties']
    assert 'new_string' in params['properties']
    assert 'expected_replacements' in params['properties']
    assert 'content' in params['properties']
    assert 'offset' in params['properties']
    assert 'limit' in params['properties']
    assert 'ignore' in params['properties']  # list_directory parameter
    assert 'respect_git_ignore' in params['properties']  # list_directory parameter

    # Check command enum (updated for Gemini CLI alignment)
    command_enum = params['properties']['command']['enum']
    expected_commands = ['read_file', 'write_file', 'replace', 'list_directory']
    assert all(cmd in command_enum for cmd in expected_commands)

    # Check required parameters (only command is required, others are conditional)
    assert params['required'] == ['command']


def test_create_gemini_editor_tool_short():
    """Test creating the Gemini editor tool with short description."""
    tool = create_gemini_editor_tool(use_short_description=True)

    assert tool['type'] == 'function'
    assert tool['function']['name'] == GEMINI_EDITOR_TOOL_NAME
    assert 'Gemini-style editing tool' in tool['function']['description']

    # Short description should be shorter than detailed
    detailed_tool = create_gemini_editor_tool(use_short_description=False)
    assert len(tool['function']['description']) < len(
        detailed_tool['function']['description']
    )


def test_gemini_editor_tool_parameter_types():
    """Test that the Gemini editor tool has correct parameter types."""
    tool = create_gemini_editor_tool()
    params = tool['function']['parameters']['properties']

    # Check string parameters (updated for Gemini CLI alignment)
    string_params = [
        'command',
        'absolute_path',  # read_file parameter
        'file_path',  # write_file and replace parameter
        'path',  # list_directory parameter
        'old_string',
        'new_string',
        'content',
    ]
    for param in string_params:
        assert params[param]['type'] == 'string'

    # Check number parameters (Gemini CLI uses 'number' not 'integer')
    number_params = ['expected_replacements', 'offset', 'limit']
    for param in number_params:
        assert params[param]['type'] == 'number'

    # Check array parameter
    assert params['ignore']['type'] == 'array'
    assert params['ignore']['items']['type'] == 'string'

    # Check boolean parameter
    assert params['respect_git_ignore']['type'] == 'boolean'

    # Check minimum values for number parameters
    assert params['expected_replacements']['minimum'] == 1
    # Note: offset doesn't have minimum in Gemini CLI (can be 0)
    # Note: limit doesn't have minimum in Gemini CLI


def test_gemini_editor_tool_command_descriptions():
    """Test that command descriptions are appropriate."""
    tool = create_gemini_editor_tool()
    command_desc = tool['function']['parameters']['properties']['command'][
        'description'
    ]

    # Check for Gemini CLI-aligned commands
    assert 'read_file' in command_desc
    assert 'write_file' in command_desc
    assert 'replace' in command_desc
    assert 'list_directory' in command_desc
