"""Tests for MCP configuration screen functionality."""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch, call
from io import StringIO

import pytest

from openhands_cli.locations import MCP_CONFIG_FILE
from openhands_cli.tui.settings.mcp_screen import MCPScreen
from openhands.sdk import Agent, LLM

@pytest.fixture
def persistence_dir(tmp_path, monkeypatch):
    """Patch PERSISTENCE_DIR to tmp and return the directory Path."""
    monkeypatch.setattr(
        "openhands_cli.tui.settings.mcp_screen.PERSISTENCE_DIR",
        str(tmp_path),
        raising=True,
    )
    return tmp_path



class TestMCPScreen:
    """Test the MCP screen display functionality."""

    def _create_agent(self, mcp_config=None):
        """Helper to create an agent with optional MCP config."""
        if mcp_config is None:
            mcp_config = {}
        return Agent(
            llm=LLM(model="test-model", api_key="test-key", service_id='test-service'),
            tools=[],
            mcp_config=mcp_config
        )

    def _create_mcp_config_file(self, tmp_path, config):
        """Helper to create an MCP config file."""
        config_file = tmp_path / MCP_CONFIG_FILE
        config_file.write_text(json.dumps(config))
        return config_file

    @patch('openhands_cli.tui.settings.mcp_screen.print_formatted_text')
    def test_mcp_help_instruction_always_shown(self, mock_print, persistence_dir):
        """Test that the MCP help instruction is always shown."""
        screen = MCPScreen()
        agent = self._create_agent()

        screen.display_mcp_info(agent)

        # Check that help instructions are displayed
        all_calls = [str(call_args) for call_args in mock_print.call_args_list]
        help_content = ' '.join(all_calls)

        assert "MCP (Model Context Protocol) Configuration" in help_content
        assert "To get started:" in help_content
        assert "~/.openhands/mcp.json" in help_content
        assert "https://gofastmcp.com/clients/client#configuration-format" in help_content
        assert "Restart your OpenHands session" in help_content

    @patch('openhands_cli.tui.settings.mcp_screen.print_formatted_text')
    def test_agent_current_mcp_servers_always_displayed(self, mock_print, persistence_dir):
        """Test that the agent's current MCP servers are always displayed."""
        # Agent with existing MCP servers
        agent = self._create_agent({
            'mcpServers': {
                'existing_server': {
                    'command': 'python',
                    'args': ['-m', 'existing_server']
                }
            }
        })

        screen = MCPScreen()
        screen.display_mcp_info(agent)

        # Check that current agent servers are displayed
        all_calls = [str(call_args) for call_args in mock_print.call_args_list]
        content = ' '.join(all_calls)

        assert "Current Agent MCP Servers:" in content
        assert "existing_server" in content

    @patch('openhands_cli.tui.settings.mcp_screen.print_formatted_text')
    def test_agent_no_current_mcp_servers_displayed(self, mock_print, persistence_dir):
        """Test that when agent has no MCP servers, appropriate message is shown."""
        agent = self._create_agent()  # No MCP config
        screen = MCPScreen()
        screen.display_mcp_info(agent)

        # Check that "None configured" message is displayed
        all_calls = [str(call_args) for call_args in mock_print.call_args_list]
        content = ' '.join(all_calls)

        assert "Current Agent MCP Servers:" in content
        assert "None configured on the current agent" in content

    @patch('openhands_cli.tui.settings.mcp_screen.print_formatted_text')
    def test_show_new_servers_from_mcp_json(self, mock_print, persistence_dir):
        """Test that new servers from mcp.json are shown as requiring restart."""
        # Agent with no existing servers
        agent = self._create_agent()

        # Create mcp.json with new servers
        mcp_config = {
            "mcpServers": {
                "fetch": {
                    "command": "uvx",
                    "args": ["mcp-server-fetch"]
                },
                "notion": {
                    "url": "https://mcp.notion.com/mcp",
                    "auth": "oauth"
                }
            }
        }
        self._create_mcp_config_file(persistence_dir, mcp_config)

        screen = MCPScreen()
        screen.display_mcp_info(agent)

        all_calls = [str(call_args) for call_args in mock_print.call_args_list]
        content = ' '.join(all_calls)

        assert "Incoming Servers on Restart" in content
        assert "New servers (will be added):" in content
        assert "fetch" in content
        assert "notion" in content

    @patch('openhands_cli.tui.settings.mcp_screen.print_formatted_text')
    def test_show_overriding_servers_from_mcp_json(self, mock_print, persistence_dir):
        """Test that overriding servers from mcp.json are shown as requiring restart."""
        # Agent with existing server
        agent = self._create_agent({
            'mcpServers': {
                'fetch': {
                    'command': 'python',
                    'args': ['-m', 'old_fetch_server']
                }
            }
        })

        # Create mcp.json with updated server config
        mcp_config = {
            "mcpServers": {
                "fetch": {
                    "command": "uvx",
                    "args": ["mcp-server-fetch"]
                }
            }
        }
        self._create_mcp_config_file(persistence_dir, mcp_config)

        screen = MCPScreen()
        screen.display_mcp_info(agent)

        all_calls = [str(call_args) for call_args in mock_print.call_args_list]
        content = ' '.join(all_calls)

        assert "Incoming Servers on Restart" in content
        assert "Updated servers (configuration will change):" in content
        assert "fetch" in content
        assert "Current:" in content
        assert "Incoming:" in content

    @patch('openhands_cli.tui.settings.mcp_screen.print_formatted_text')
    def test_show_all_servers_already_synced_message(self, mock_print, persistence_dir):
        """Test that when all mcp.json servers are already in agent, no sync required message is shown."""
        # Agent with existing server
        agent = self._create_agent({
            'mcpServers': {
                'fetch': {
                    'command': 'uvx',
                    'args': ['mcp-server-fetch'],
                    'env': {},
                    'transport': 'stdio'
                }
            }
        })

        # Create mcp.json with same server config
        mcp_config = {
            "mcpServers": {
                "fetch": {
                    "command": "uvx",
                    "args": ["mcp-server-fetch"]
                }
            }
        }
        self._create_mcp_config_file(persistence_dir, mcp_config)

        screen = MCPScreen()
        screen.display_mcp_info(agent)

        all_calls = [str(call_args) for call_args in mock_print.call_args_list]
        content = ' '.join(all_calls)

        assert "Incoming Servers on Restart" in content
        assert "All configured servers match the current agent configuration" in content

    @patch('openhands_cli.tui.settings.mcp_screen.print_formatted_text')
    def test_invalid_mcp_json_file_handling(self, mock_print, persistence_dir):
        """Test that invalid mcp.json file is handled gracefully."""
        agent = self._create_agent()

        # Create invalid JSON file
        config_file = persistence_dir / MCP_CONFIG_FILE
        config_file.write_text('{"invalid": json content}')  # Invalid JSON

        screen = MCPScreen()
        screen.display_mcp_info(agent)

        all_calls = [str(call_args) for call_args in mock_print.call_args_list]
        content = ' '.join(all_calls)

        assert "Invalid MCP configuration file" in content
        assert "Please check your configuration file format" in content

    @patch('openhands_cli.tui.settings.mcp_screen.print_formatted_text')
    def test_missing_mcp_json_file_handling(self, mock_print, persistence_dir):
        """Test that missing mcp.json file is handled gracefully."""
        agent = self._create_agent()
        screen = MCPScreen()
        screen.display_mcp_info(agent)

        all_calls = [str(call_args) for call_args in mock_print.call_args_list]
        content = ' '.join(all_calls)

        assert "Configuration file not found" in content
        assert "No incoming servers detected for next restart" in content
