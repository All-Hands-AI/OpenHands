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

    # Check parameters
    params = tool['function']['parameters']
    assert params['type'] == 'object'
    assert 'command' in params['properties']
    assert 'path' in params['properties']
    assert 'old_string' in params['properties']
    assert 'new_string' in params['properties']
    assert 'expected_replacements' in params['properties']
    assert 'content' in params['properties']
    assert 'offset' in params['properties']
    assert 'limit' in params['properties']
    assert 'view_range' in params['properties']

    # Check command enum
    command_enum = params['properties']['command']['enum']
    expected_commands = ['view', 'create', 'replace', 'write_file', 'read_file']
    assert all(cmd in command_enum for cmd in expected_commands)

    # Check required parameters
    assert params['required'] == ['command', 'path']


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

    # Check string parameters
    string_params = [
        'command',
        'path',
        'file_text',
        'old_string',
        'new_string',
        'content',
    ]
    for param in string_params:
        assert params[param]['type'] == 'string'

    # Check integer parameters
    integer_params = ['expected_replacements', 'offset', 'limit']
    for param in integer_params:
        assert params[param]['type'] == 'integer'

    # Check array parameter
    assert params['view_range']['type'] == 'array'
    assert params['view_range']['items']['type'] == 'integer'

    # Check minimum values for integer parameters
    assert params['expected_replacements']['minimum'] == 1
    assert params['offset']['minimum'] == 0
    assert params['limit']['minimum'] == 1


def test_gemini_editor_tool_command_descriptions():
    """Test that command descriptions are appropriate."""
    tool = create_gemini_editor_tool()
    command_desc = tool['function']['parameters']['properties']['command'][
        'description'
    ]

    assert 'view' in command_desc
    assert 'create' in command_desc
    assert 'replace' in command_desc
    assert 'write_file' in command_desc
    assert 'read_file' in command_desc
