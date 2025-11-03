import sys
from unittest.mock import patch

import pytest

from openhands.agenthub.codeact_agent.codeact_agent import CodeActAgent
from openhands.core.config import AgentConfig
from openhands.llm.llm import LLM

# Skip all tests in this module if not running on Windows
pytestmark = pytest.mark.skipif(
    sys.platform != "win32", reason="Windows prompt refinement tests require Windows"
)


@pytest.fixture
def mock_llm():
    """Create a mock LLM for testing."""
    llm = LLM(config={"model": "gpt-4", "api_key": "test"})
    return llm


@pytest.fixture
def agent_config():
    """Create a basic agent config for testing."""
    return AgentConfig()


def test_codeact_agent_system_prompt_no_bash_on_windows(mock_llm, agent_config):
    """Test that CodeActAgent's system prompt doesn't contain 'bash' on Windows."""
    # Create a CodeActAgent instance
    agent = CodeActAgent(llm=mock_llm, config=agent_config)

    # Get the system prompt
    system_prompt = agent.prompt_manager.get_system_message()

    # Assert that 'bash' doesn't exist in the system prompt (case-insensitive)
    assert "bash" not in system_prompt.lower(), (
        f"System prompt contains 'bash' on Windows platform. "
        f"It should be replaced with 'powershell'. "
        f"System prompt: {system_prompt}"
    )

    # Verify that 'powershell' exists instead (case-insensitive)
    assert "powershell" in system_prompt.lower(), (
        f"System prompt should contain 'powershell' on Windows platform. "
        f"System prompt: {system_prompt}"
    )


def test_codeact_agent_tool_descriptions_no_bash_on_windows(mock_llm, agent_config):
    """Test that CodeActAgent's tool descriptions don't contain 'bash' on Windows."""
    # Create a CodeActAgent instance
    agent = CodeActAgent(llm=mock_llm, config=agent_config)

    # Get the tools
    tools = agent.tools

    # Check each tool's description and parameters
    for tool in tools:
        if tool["type"] == "function":
            function_info = tool["function"]

            # Check function description
            description = function_info.get("description", "")
            assert "bash" not in description.lower(), (
                f"Tool '{function_info['name']}' description contains 'bash' on Windows. "
                f"Description: {description}"
            )

            # Check parameter descriptions
            parameters = function_info.get("parameters", {})
            properties = parameters.get("properties", {})

            for param_name, param_info in properties.items():
                param_description = param_info.get("description", "")
                assert "bash" not in param_description.lower(), (
                    f"Tool '{function_info['name']}' parameter '{param_name}' "
                    f"description contains 'bash' on Windows. "
                    f"Parameter description: {param_description}"
                )


def test_in_context_learning_example_no_bash_on_windows():
    """Test that in-context learning examples don't contain 'bash' on Windows."""
    from openhands.agenthub.codeact_agent.tools.bash import create_cmd_run_tool
    from openhands.agenthub.codeact_agent.tools.finish import FinishTool
    from openhands.agenthub.codeact_agent.tools.str_replace_editor import (
        create_str_replace_editor_tool,
    )
    from openhands.llm.fn_call_converter import get_example_for_tools

    # Create a sample set of tools
    tools = [
        create_cmd_run_tool(),
        create_str_replace_editor_tool(),
        FinishTool,
    ]

    # Get the in-context learning example
    example = get_example_for_tools(tools)

    # Assert that 'bash' doesn't exist in the example (case-insensitive)
    assert "bash" not in example.lower(), (
        f"In-context learning example contains 'bash' on Windows platform. "
        f"It should be replaced with 'powershell'. "
        f"Example: {example}"
    )

    # Verify that 'powershell' exists instead (case-insensitive)
    if example:  # Only check if example is not empty
        assert "powershell" in example.lower(), (
            f"In-context learning example should contain 'powershell' on Windows platform. "
            f"Example: {example}"
        )


def test_refine_prompt_function_works():
    """Test that the refine_prompt function correctly replaces 'bash' with 'powershell'."""
    from openhands.agenthub.codeact_agent.tools.bash import refine_prompt

    # Test basic replacement
    test_prompt = "Execute a bash command to list files"
    refined_prompt = refine_prompt(test_prompt)

    assert "bash" not in refined_prompt.lower()
    assert "powershell" in refined_prompt.lower()
    assert refined_prompt == "Execute a powershell command to list files"

    # Test multiple occurrences
    test_prompt = "Use bash to run bash commands in the bash shell"
    refined_prompt = refine_prompt(test_prompt)

    assert "bash" not in refined_prompt.lower()
    assert (
        refined_prompt
        == "Use powershell to run powershell commands in the powershell shell"
    )

    # Test case sensitivity
    test_prompt = "BASH and Bash and bash should all be replaced"
    refined_prompt = refine_prompt(test_prompt)

    assert "bash" not in refined_prompt.lower()
    assert (
        refined_prompt
        == "powershell and powershell and powershell should all be replaced"
    )

    # Test execute_bash tool name replacement
    test_prompt = "Use the execute_bash tool to run commands"
    refined_prompt = refine_prompt(test_prompt)

    assert "execute_bash" not in refined_prompt.lower()
    assert "execute_powershell" in refined_prompt.lower()
    assert refined_prompt == "Use the execute_powershell tool to run commands"

    # Test that words containing 'bash' but not equal to 'bash' are preserved
    test_prompt = "The bashful person likes bash-like syntax"
    refined_prompt = refine_prompt(test_prompt)

    # 'bashful' should be preserved, 'bash-like' should become 'powershell-like'
    assert "bashful" in refined_prompt
    assert "powershell-like" in refined_prompt
    assert refined_prompt == "The bashful person likes powershell-like syntax"


def test_refine_prompt_function_on_non_windows():
    """Test that the refine_prompt function doesn't change anything on non-Windows platforms."""
    from openhands.agenthub.codeact_agent.tools.bash import refine_prompt

    # Mock sys.platform to simulate non-Windows
    with patch("openhands.agenthub.codeact_agent.tools.bash.sys.platform", "linux"):
        test_prompt = "Execute a bash command to list files"
        refined_prompt = refine_prompt(test_prompt)

        # On non-Windows, the prompt should remain unchanged
        assert refined_prompt == test_prompt
        assert "bash" in refined_prompt.lower()
