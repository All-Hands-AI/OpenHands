"""Integration tests for the Gemini editor tool with CodeAct agent."""

from openhands.agenthub.codeact_agent.codeact_agent import CodeActAgent
from openhands.core.config.agent_config import AgentConfig

# Gemini CLI tool names
GEMINI_TOOL_NAMES = ['read_file', 'write_file', 'replace', 'list_directory']


class MockLLM:
    """Mock LLM for testing."""

    def __init__(self, model_name: str = 'test-model'):
        self.config = type('Config', (), {'model': model_name})()


def test_gemini_editor_integration_with_codeact_agent():
    """Test that the Gemini editor integrates correctly with CodeAct agent."""
    config = AgentConfig(
        enable_gemini_editor=True,
        enable_editor=False,
        enable_llm_editor=False,
    )

    agent = CodeActAgent(MockLLM(), config)
    tools = agent._get_tools()

    # Find all Gemini tools
    tool_names = [tool['function']['name'] for tool in tools]

    # Verify all four Gemini CLI tools are included
    for tool_name in GEMINI_TOOL_NAMES:
        assert tool_name in tool_names, f'Gemini tool {tool_name} should be included'

    # Verify tool structures
    gemini_tools = [
        tool for tool in tools if tool['function']['name'] in GEMINI_TOOL_NAMES
    ]
    assert len(gemini_tools) == 4, 'All four Gemini CLI tools should be included'

    for tool in gemini_tools:
        assert tool['type'] == 'function'
        assert tool['function']['name'] in GEMINI_TOOL_NAMES


def test_gemini_editor_priority_over_standard_editor():
    """Test that Gemini editor takes priority over standard editor."""
    config = AgentConfig(
        enable_gemini_editor=True,
        enable_editor=True,
        enable_llm_editor=False,
    )

    agent = CodeActAgent(MockLLM(), config)
    tools = agent._get_tools()

    tool_names = [tool['function']['name'] for tool in tools]

    # Verify all Gemini tools are present
    for tool_name in GEMINI_TOOL_NAMES:
        assert tool_name in tool_names, f'Gemini tool {tool_name} should be included'

    # Verify standard editor is not included
    assert 'str_replace_editor' not in tool_names


def test_gemini_editor_with_short_description():
    """Test that Gemini editor uses short description for certain models."""
    # Test with a model that should use short descriptions
    config = AgentConfig(enable_gemini_editor=True, enable_editor=False)
    agent = CodeActAgent(MockLLM('gpt-4'), config)
    tools = agent._get_tools()

    # Find Gemini tools
    gemini_tools = [
        tool for tool in tools if tool['function']['name'] in GEMINI_TOOL_NAMES
    ]
    assert len(gemini_tools) == 4, 'All four Gemini CLI tools should be included'

    # The descriptions should be shorter for GPT models
    for tool in gemini_tools:
        description = tool['function']['description']
        assert len(description) < 2000  # Short description should be much shorter


def test_gemini_editor_disabled():
    """Test that Gemini editor is not included when disabled."""
    config = AgentConfig(
        enable_gemini_editor=False,
        enable_editor=True,
        enable_llm_editor=False,
    )

    agent = CodeActAgent(MockLLM(), config)
    tools = agent._get_tools()

    tool_names = [tool['function']['name'] for tool in tools]

    # Verify no Gemini tools are present
    for tool_name in GEMINI_TOOL_NAMES:
        assert tool_name not in tool_names, (
            f'Gemini tool {tool_name} should not be included'
        )

    assert 'str_replace_editor' in tool_names  # Standard editor should be used


def test_gemini_editor_parameter_validation():
    """Test that the Gemini editor tools have correct parameter validation."""
    config = AgentConfig(enable_gemini_editor=True, enable_editor=False)
    agent = CodeActAgent(MockLLM(), config)
    tools = agent._get_tools()

    # Find all Gemini tools
    gemini_tools = {
        tool['function']['name']: tool
        for tool in tools
        if tool['function']['name'] in GEMINI_TOOL_NAMES
    }
    assert len(gemini_tools) == 4, 'All four Gemini CLI tools should be included'

    # Test read_file tool
    read_file_tool = gemini_tools['read_file']
    read_params = read_file_tool['function']['parameters']
    read_props = read_params['properties']
    assert read_params['required'] == ['absolute_path']
    assert read_props['absolute_path']['type'] == 'string'
    assert read_props['offset']['type'] == 'number'
    assert read_props['limit']['type'] == 'number'

    # Test write_file tool
    write_file_tool = gemini_tools['write_file']
    write_params = write_file_tool['function']['parameters']
    write_props = write_params['properties']
    assert write_params['required'] == ['file_path', 'content']
    assert write_props['file_path']['type'] == 'string'
    assert write_props['content']['type'] == 'string'

    # Test replace tool
    replace_tool = gemini_tools['replace']
    replace_params = replace_tool['function']['parameters']
    replace_props = replace_params['properties']
    assert replace_params['required'] == ['file_path', 'old_string', 'new_string']
    assert replace_props['file_path']['type'] == 'string'
    assert replace_props['old_string']['type'] == 'string'
    assert replace_props['new_string']['type'] == 'string'
    assert replace_props['expected_replacements']['type'] == 'number'
    assert replace_props['expected_replacements']['minimum'] == 1

    # Test list_directory tool
    list_dir_tool = gemini_tools['list_directory']
    list_params = list_dir_tool['function']['parameters']
    list_props = list_params['properties']
    assert list_params['required'] == ['path']
    assert list_props['path']['type'] == 'string'
    assert list_props['ignore']['type'] == 'array'
    assert list_props['ignore']['items']['type'] == 'string'
    assert list_props['respect_git_ignore']['type'] == 'boolean'


def test_all_editor_types_mutually_exclusive():
    """Test that only one editor type is active at a time."""
    # Test all combinations to ensure mutual exclusivity
    test_cases = [
        # (llm, gemini, standard) -> expected_tools
        (True, True, True, ['edit_file']),  # LLM has highest priority
        (True, True, False, ['edit_file']),  # LLM has highest priority
        (True, False, True, ['edit_file']),  # LLM has highest priority
        (True, False, False, ['edit_file']),  # LLM has highest priority
        (False, True, True, GEMINI_TOOL_NAMES),  # Gemini has second priority
        (False, True, False, GEMINI_TOOL_NAMES),  # Gemini has second priority
        (False, False, True, ['str_replace_editor']),  # Standard has lowest priority
        (False, False, False, []),  # No editor
    ]

    for llm, gemini, standard, expected in test_cases:
        config = AgentConfig(
            enable_llm_editor=llm,
            enable_gemini_editor=gemini,
            enable_editor=standard,
        )

        agent = CodeActAgent(MockLLM(), config)
        tools = agent._get_tools()

        all_editor_tools = ['edit_file'] + GEMINI_TOOL_NAMES + ['str_replace_editor']
        editor_tools = [
            tool['function']['name']
            for tool in tools
            if tool['function']['name'] in all_editor_tools
        ]

        if not expected:
            assert len(editor_tools) == 0, (
                f'No editor should be active for config {(llm, gemini, standard)}'
            )
        else:
            assert set(editor_tools) == set(expected), (
                f'Expected {expected} for config {(llm, gemini, standard)}, got {editor_tools}'
            )
