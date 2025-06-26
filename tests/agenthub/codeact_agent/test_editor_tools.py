"""Tests for editor tool selection in CodeActAgent."""

import pytest
from unittest.mock import patch, MagicMock

from openhands.agenthub.codeact_agent.codeact_agent import CodeActAgent
from openhands.core.config import AgentConfig
from openhands.llm.tool_names import (
    CLAUDE_EDITOR_TOOL_NAME,
    GEMINI_EDIT_TOOL_NAME,
    GEMINI_READ_FILE_TOOL_NAME,
    GEMINI_WRITE_FILE_TOOL_NAME,
    STR_REPLACE_EDITOR_TOOL_NAME,
    LLM_BASED_EDIT_TOOL_NAME,
)


def get_tool_names(tools):
    """Extract tool names from the tools list."""
    tool_names = []
    for tool in tools:
        if isinstance(tool, dict) and 'function' in tool:
            tool_names.append(tool['function']['name'])
        elif hasattr(tool, 'function') and hasattr(tool.function, 'name'):
            tool_names.append(tool.function.name)
    return tool_names


@pytest.mark.parametrize(
    "config_params,expected_tools,unexpected_tools",
    [
        # Test with all editors disabled
        (
            {"enable_editor": False},
            [],
            [
                STR_REPLACE_EDITOR_TOOL_NAME,
                CLAUDE_EDITOR_TOOL_NAME,
                GEMINI_EDIT_TOOL_NAME,
                GEMINI_WRITE_FILE_TOOL_NAME,
                GEMINI_READ_FILE_TOOL_NAME,
                LLM_BASED_EDIT_TOOL_NAME,
            ],
        ),
        # Test with only LLM editor enabled
        (
            {"enable_llm_editor": True},
            [LLM_BASED_EDIT_TOOL_NAME],
            [
                STR_REPLACE_EDITOR_TOOL_NAME,
                CLAUDE_EDITOR_TOOL_NAME,
                GEMINI_EDIT_TOOL_NAME,
                GEMINI_WRITE_FILE_TOOL_NAME,
                GEMINI_READ_FILE_TOOL_NAME,
            ],
        ),
        # Test with only Claude editor enabled
        (
            {"enable_claude_editor": True, "enable_gemini_editor": False},
            [CLAUDE_EDITOR_TOOL_NAME],
            [
                STR_REPLACE_EDITOR_TOOL_NAME,
                GEMINI_EDIT_TOOL_NAME,
                GEMINI_WRITE_FILE_TOOL_NAME,
                GEMINI_READ_FILE_TOOL_NAME,
                LLM_BASED_EDIT_TOOL_NAME,
            ],
        ),
        # Test with only Gemini editor enabled
        (
            {"enable_claude_editor": False, "enable_gemini_editor": True},
            [
                GEMINI_EDIT_TOOL_NAME,
                GEMINI_WRITE_FILE_TOOL_NAME,
                GEMINI_READ_FILE_TOOL_NAME,
            ],
            [
                STR_REPLACE_EDITOR_TOOL_NAME,
                CLAUDE_EDITOR_TOOL_NAME,
                LLM_BASED_EDIT_TOOL_NAME,
            ],
        ),
        # Test with both Claude and Gemini editors enabled
        (
            {"enable_claude_editor": True, "enable_gemini_editor": True},
            [
                CLAUDE_EDITOR_TOOL_NAME,
                GEMINI_EDIT_TOOL_NAME,
                GEMINI_WRITE_FILE_TOOL_NAME,
                GEMINI_READ_FILE_TOOL_NAME,
            ],
            [
                STR_REPLACE_EDITOR_TOOL_NAME,
                LLM_BASED_EDIT_TOOL_NAME,
            ],
        ),
        # Test legacy behavior (str_replace_editor only)
        (
            {},  # Default config
            [STR_REPLACE_EDITOR_TOOL_NAME],
            [
                CLAUDE_EDITOR_TOOL_NAME,
                GEMINI_EDIT_TOOL_NAME,
                GEMINI_WRITE_FILE_TOOL_NAME,
                GEMINI_READ_FILE_TOOL_NAME,
                LLM_BASED_EDIT_TOOL_NAME,
            ],
        ),
    ],
)
def test_editor_tool_selection(config_params, expected_tools, unexpected_tools):
    """Test that the correct editor tools are selected based on configuration."""
    # Create config with the specified parameters
    config = AgentConfig(**config_params)
    
    # Create a mock LLM
    mock_llm = MagicMock()
    mock_llm.config.model = "test-model"
    
    # Create the agent with the config and mock LLM
    agent = CodeActAgent(config=config, llm=mock_llm)
    
    # Get the tools
    tools = agent._get_tools()
    tool_names = get_tool_names(tools)
    
    # Check that expected tools are present
    for tool_name in expected_tools:
        assert tool_name in tool_names, f"Expected tool {tool_name} to be present"
    
    # Check that unexpected tools are not present
    for tool_name in unexpected_tools:
        assert tool_name not in tool_names, f"Unexpected tool {tool_name} is present"