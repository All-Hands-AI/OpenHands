"""Tests for MCP action functionality."""

import pytest
from unittest.mock import patch, MagicMock
import sys
import os

# Add the project root to the path to import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Import the MCP action module directly to avoid SDK dependency issues
import importlib.util

def load_mcp_action_module():
    """Load the MCP action module directly."""
    mcp_action_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), 
        'openhands_cli', 'user_actions', 'mcp_action.py'
    )
    spec = importlib.util.spec_from_file_location('mcp_action', mcp_action_path)
    module = importlib.util.module_from_spec(spec)
    
    # Mock the problematic imports
    with patch.dict('sys.modules', {
        'openhands_cli.user_actions.utils': MagicMock(),
        'openhands_cli.tui.utils': MagicMock(),
        'prompt_toolkit.validation': MagicMock(),
        'prompt_toolkit': MagicMock(),
        'prompt_toolkit.formatted_text': MagicMock(),
    }):
        spec.loader.exec_module(module)
    
    return module


class TestMCPAction:
    """Test the MCP action functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mcp_action = load_mcp_action_module()
        # Clear the servers dict for each test
        self.mcp_action._mcp_servers.clear()

    def test_initial_state(self):
        """Test that MCP starts with empty configuration."""
        assert self.mcp_action._mcp_servers == {}
        assert self.mcp_action.get_mcp_config() == {}

    def test_mcp_action_type_enum(self):
        """Test that MCPActionType enum has correct values."""
        action_types = [e.value for e in self.mcp_action.MCPActionType]
        expected_types = ['list', 'add', 'remove', 'go_back']
        assert set(action_types) == set(expected_types)

    def test_mcp_server_type_enum(self):
        """Test that MCPServerType enum has correct values."""
        server_types = [e.value for e in self.mcp_action.MCPServerType]
        expected_types = ['command', 'url']
        assert set(server_types) == set(expected_types)

    def test_add_command_based_server(self):
        """Test adding a command-based MCP server."""
        self.mcp_action._mcp_servers['fetch'] = {
            'command': 'uvx',
            'args': ['mcp-server-fetch']
        }
        
        config = self.mcp_action.get_mcp_config()
        expected = {
            "mcpServers": {
                "fetch": {
                    "command": "uvx",
                    "args": ["mcp-server-fetch"]
                }
            }
        }
        assert config == expected

    def test_add_url_based_server(self):
        """Test adding a URL-based MCP server."""
        self.mcp_action._mcp_servers['notion'] = {
            'url': 'https://mcp.notion.com/mcp',
            'auth': 'oauth'
        }
        
        config = self.mcp_action.get_mcp_config()
        expected = {
            "mcpServers": {
                "notion": {
                    "url": "https://mcp.notion.com/mcp",
                    "auth": "oauth"
                }
            }
        }
        assert config == expected

    def test_add_url_based_server_without_auth(self):
        """Test adding a URL-based MCP server without auth."""
        self.mcp_action._mcp_servers['simple'] = {
            'url': 'https://example.com/mcp'
        }
        
        config = self.mcp_action.get_mcp_config()
        expected = {
            "mcpServers": {
                "simple": {
                    "url": "https://example.com/mcp"
                }
            }
        }
        assert config == expected

    def test_multiple_servers(self):
        """Test configuration with multiple servers."""
        self.mcp_action._mcp_servers['fetch'] = {
            'command': 'uvx',
            'args': ['mcp-server-fetch']
        }
        self.mcp_action._mcp_servers['notion'] = {
            'url': 'https://mcp.notion.com/mcp',
            'auth': 'oauth'
        }
        self.mcp_action._mcp_servers['simple'] = {
            'url': 'https://example.com/mcp'
        }
        
        config = self.mcp_action.get_mcp_config()
        expected = {
            "mcpServers": {
                "fetch": {
                    "command": "uvx",
                    "args": ["mcp-server-fetch"]
                },
                "notion": {
                    "url": "https://mcp.notion.com/mcp",
                    "auth": "oauth"
                },
                "simple": {
                    "url": "https://example.com/mcp"
                }
            }
        }
        assert config == expected

    def test_command_server_without_args(self):
        """Test command-based server without args."""
        self.mcp_action._mcp_servers['simple_cmd'] = {
            'command': 'mcp-server'
        }
        
        config = self.mcp_action.get_mcp_config()
        expected = {
            "mcpServers": {
                "simple_cmd": {
                    "command": "mcp-server",
                    "args": []
                }
            }
        }
        assert config == expected

    def test_empty_config_returns_empty_dict(self):
        """Test that empty server list returns empty dict."""
        config = self.mcp_action.get_mcp_config()
        assert config == {}

    def test_config_format_matches_agent_sdk_examples(self):
        """Test that the config format matches the agent-sdk examples."""
        # Add servers similar to the examples from agent-sdk
        self.mcp_action._mcp_servers['fetch'] = {
            'command': 'uvx',
            'args': ['mcp-server-fetch']
        }
        self.mcp_action._mcp_servers['filesystem'] = {
            'command': 'npx',
            'args': ['-y', '@modelcontextprotocol/server-filesystem', '/path/to/allowed/files']
        }
        
        config = self.mcp_action.get_mcp_config()
        
        # Verify structure matches what agent-sdk expects
        assert 'mcpServers' in config
        assert isinstance(config['mcpServers'], dict)
        
        # Verify fetch server
        fetch_config = config['mcpServers']['fetch']
        assert fetch_config['command'] == 'uvx'
        assert fetch_config['args'] == ['mcp-server-fetch']
        
        # Verify filesystem server
        fs_config = config['mcpServers']['filesystem']
        assert fs_config['command'] == 'npx'
        assert fs_config['args'] == ['-y', '@modelcontextprotocol/server-filesystem', '/path/to/allowed/files']