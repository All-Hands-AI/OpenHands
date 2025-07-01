"""Integration tests for the Gemini editor tool with CodeAct agent."""

from openhands.agenthub.codeact_agent.codeact_agent import CodeActAgent
from openhands.core.config.agent_config import AgentConfig
from openhands.llm.tool_names import GEMINI_EDITOR_TOOL_NAME


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

    # Find the Gemini editor tool
    gemini_tool = None
    for tool in tools:
        if tool['function']['name'] == GEMINI_EDITOR_TOOL_NAME:
            gemini_tool = tool
            break

    assert gemini_tool is not None, 'Gemini editor tool should be included'

    # Verify tool structure
    assert gemini_tool['type'] == 'function'
    assert gemini_tool['function']['name'] == GEMINI_EDITOR_TOOL_NAME

    # Verify all expected commands are available (updated for Gemini CLI alignment)
    params = gemini_tool['function']['parameters']
    command_enum = params['properties']['command']['enum']
    expected_commands = ['read_file', 'write_file', 'replace', 'list_directory']

    for cmd in expected_commands:
        assert cmd in command_enum, f"Command '{cmd}' should be available"


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

    assert GEMINI_EDITOR_TOOL_NAME in tool_names
    assert 'str_replace_editor' not in tool_names


def test_gemini_editor_with_short_description():
    """Test that Gemini editor uses short description for certain models."""
    # Test with a model that should use short descriptions
    config = AgentConfig(enable_gemini_editor=True, enable_editor=False)
    agent = CodeActAgent(MockLLM('gpt-4'), config)
    tools = agent._get_tools()

    gemini_tool = None
    for tool in tools:
        if tool['function']['name'] == GEMINI_EDITOR_TOOL_NAME:
            gemini_tool = tool
            break

    assert gemini_tool is not None

    # The description should be shorter for GPT models
    description = gemini_tool['function']['description']
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

    assert GEMINI_EDITOR_TOOL_NAME not in tool_names
    assert 'str_replace_editor' in tool_names  # Standard editor should be used


def test_gemini_editor_parameter_validation():
    """Test that the Gemini editor tool has correct parameter validation."""
    config = AgentConfig(enable_gemini_editor=True, enable_editor=False)
    agent = CodeActAgent(MockLLM(), config)
    tools = agent._get_tools()

    gemini_tool = None
    for tool in tools:
        if tool['function']['name'] == GEMINI_EDITOR_TOOL_NAME:
            gemini_tool = tool
            break

    assert gemini_tool is not None

    params = gemini_tool['function']['parameters']
    properties = params['properties']

    # Test required parameters (updated for Gemini CLI alignment)
    assert params['required'] == ['command']

    # Test parameter types (updated for Gemini CLI alignment)
    assert properties['command']['type'] == 'string'
    assert properties['absolute_path']['type'] == 'string'  # read_file parameter
    assert (
        properties['file_path']['type'] == 'string'
    )  # write_file and replace parameter
    assert properties['path']['type'] == 'string'  # list_directory parameter
    assert properties['old_string']['type'] == 'string'
    assert properties['new_string']['type'] == 'string'
    assert properties['content']['type'] == 'string'
    assert (
        properties['expected_replacements']['type'] == 'number'
    )  # Gemini CLI uses 'number'
    assert properties['offset']['type'] == 'number'  # Gemini CLI uses 'number'
    assert properties['limit']['type'] == 'number'  # Gemini CLI uses 'number'
    assert properties['ignore']['type'] == 'array'  # list_directory parameter
    assert (
        properties['respect_git_ignore']['type'] == 'boolean'
    )  # list_directory parameter

    # Test minimum values (updated for Gemini CLI alignment)
    assert properties['expected_replacements']['minimum'] == 1
    # Note: offset and limit don't have minimum constraints in Gemini CLI

    # Test array item type
    assert properties['ignore']['items']['type'] == 'string'


def test_all_editor_types_mutually_exclusive():
    """Test that only one editor type is active at a time."""
    # Test all combinations to ensure mutual exclusivity
    test_cases = [
        # (llm, gemini, standard) -> expected_tool
        (True, True, True, 'edit_file'),  # LLM has highest priority
        (True, True, False, 'edit_file'),  # LLM has highest priority
        (True, False, True, 'edit_file'),  # LLM has highest priority
        (True, False, False, 'edit_file'),  # LLM has highest priority
        (False, True, True, GEMINI_EDITOR_TOOL_NAME),  # Gemini has second priority
        (False, True, False, GEMINI_EDITOR_TOOL_NAME),  # Gemini has second priority
        (False, False, True, 'str_replace_editor'),  # Standard has lowest priority
        (False, False, False, None),  # No editor
    ]

    for llm, gemini, standard, expected in test_cases:
        config = AgentConfig(
            enable_llm_editor=llm,
            enable_gemini_editor=gemini,
            enable_editor=standard,
        )

        agent = CodeActAgent(MockLLM(), config)
        tools = agent._get_tools()

        editor_tools = [
            tool['function']['name']
            for tool in tools
            if tool['function']['name']
            in ['edit_file', GEMINI_EDITOR_TOOL_NAME, 'str_replace_editor']
        ]

        if expected is None:
            assert len(editor_tools) == 0, (
                f'No editor should be active for config {(llm, gemini, standard)}'
            )
        else:
            assert len(editor_tools) == 1, (
                f'Exactly one editor should be active for config {(llm, gemini, standard)}'
            )
            assert editor_tools[0] == expected, (
                f'Expected {expected} for config {(llm, gemini, standard)}, got {editor_tools[0]}'
            )
