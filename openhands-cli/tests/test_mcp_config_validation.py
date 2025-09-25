"""Tests for MCP configuration and agent store functionality."""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from openhands_cli.locations import AGENT_SETTINGS_PATH, MCP_CONFIG_FILE
import pytest

from openhands_cli.tui.settings.store import AgentStore
from openhands_cli.user_actions.mcp_action import check_mcp_config_status
from openhands.sdk import LocalFileStore, Agent, LLM


class TestMCPConfigStatus:
    """Test the MCP configuration status checking functionality."""

    def test_check_mcp_config_status_file_not_found(self, tmp_path):
        """Test that check_mcp_config_status handles missing config file."""
        with patch('openhands_cli.user_actions.mcp_action.PERSISTENCE_DIR', str(tmp_path)):
            status = check_mcp_config_status()
            assert not status['exists']
            assert not status['valid']
            assert status['servers'] == {}
            assert "not found" in status['message']

    def test_check_mcp_config_status_valid_config(self, tmp_path):
        """Test that check_mcp_config_status handles valid config file."""
        config_file = tmp_path / MCP_CONFIG_FILE
        valid_config = {
            "mcpServers": {
                "fetch": {
                    "command": "uvx",
                    "args": ["mcp-server-fetch"]
                }
            }
        }
        config_file.write_text(json.dumps(valid_config))
        
        with patch('openhands_cli.user_actions.mcp_action.PERSISTENCE_DIR', str(tmp_path)):
            status = check_mcp_config_status()
            assert status['exists']
            assert status['valid']
            assert len(status['servers']) == 1
            assert 'fetch' in status['servers']

    def test_check_mcp_config_status_invalid_config(self, tmp_path):
        """Test that check_mcp_config_status handles invalid config file."""
        config_file = tmp_path / MCP_CONFIG_FILE
        config_file.write_text('{"invalid": json content}')  # Invalid JSON
        
        with patch('openhands_cli.user_actions.mcp_action.PERSISTENCE_DIR', str(tmp_path)):
            status = check_mcp_config_status()
            assert status['exists']
            assert not status['valid']
            assert status['servers'] == {}
            assert "Invalid" in status['message']


def _make_store(tmp_path: Path) -> AgentStore:
    store = AgentStore()
    store.file_store = LocalFileStore(root=str(tmp_path))
    return store


def _write_agent_settings(store: AgentStore, agent: Agent) -> None:
    store.save(agent)

def _write_mcp_config_file(store: AgentStore, mcp_config: dict) -> None:
    """Write MCP configuration directly to mcp.json file."""
    store.file_store.write(MCP_CONFIG_FILE, json.dumps(mcp_config))

class TestAgentStoreMCPConfiguration:
    """Test the AgentStore MCP configuration loading functionality."""


    def test_load_mcp_configuration_file_not_found(self, tmp_path):
        """
        No mcp.json file present under store root.
        Should return {}.
        """
        store = _make_store(tmp_path)
        assert store.load_mcp_configuration() == {}

    def test_load_mcp_configuration_corrupted_file(self, tmp_path):
        """Test that load_mcp_configuration handles corrupted JSON file."""
        store = _make_store(tmp_path)
        mcp_config_file = tmp_path / MCP_CONFIG_FILE
        mcp_config_file.write_text('{"invalid": json content}')  # invalid JSON
        assert store.load_mcp_configuration() == {}

    def test_load_mcp_configuration_invalid_format(self, tmp_path):
        """Test that load_mcp_configuration handles invalid MCP config format."""
        store = _make_store(tmp_path)
        invalid_config = {"someOtherKey": "value"}  # Missing mcpServers
        _write_mcp_config_file(store, invalid_config)
        result = store.load_mcp_configuration()
        assert result == {}

    def test_load_mcp_configuration_valid_config(self, tmp_path):
        """Test that load_mcp_configuration loads valid MCP configuration."""
        # Create a valid MCP config file
        valid_config = {
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

        store = _make_store(tmp_path)
        _write_mcp_config_file(store, valid_config)

        result = store.load_mcp_configuration()

        expected = {
            "fetch": {
                "command": "uvx",
                "args": ["mcp-server-fetch"],
                "env": {},
                "transport": "stdio"
            },
            "notion": {
                "url": "https://mcp.notion.com/mcp",
                "auth": "oauth",
                "headers": {}
            }
        }
        assert result == expected

    def test_agent_store_load_combines_mcp_configs(self, tmp_path):
        """Test that AgentStore.load() combines existing MCP servers with new ones from JSON file."""
        # Create a valid MCP config file
        json_config = {
            "mcpServers": {
                "fetch": {
                    "command": "uvx",
                    "args": ["mcp-server-fetch"]
                },
            }
        }

        store = _make_store(tmp_path)

        # Create mcp config file directly
        _write_mcp_config_file(store, json_config)

        # Save agent with existing mcp servers
        agent = Agent(
            llm=LLM(model="test-model", api_key="test-key", service_id='test-service'),
            tools=[],
            mcp_config={
                'mcpServers': {
                    "existing_server": {
                        "url": "https://existing.com/mcp",
                        "auth": "none"
                    }
                }
            }
        )
        store.save(agent)

        # Load agent
        agent = store.load()
        assert agent is not None
        combined_mcp_config = agent.mcp_config['mcpServers']

        # Should contain the new server from JSON file
        assert 'fetch' in combined_mcp_config
        assert combined_mcp_config['fetch']['command'] == 'uvx'
        assert combined_mcp_config['fetch']['args'] == ['mcp-server-fetch']

        # Should also contain the existing server from agent
        assert 'existing_server' in combined_mcp_config
        assert combined_mcp_config['existing_server']['url'] == 'https://existing.com/mcp'

    def test_agent_store_load_handles_no_mcp_config_in_agent(self, tmp_path):
        """Test that AgentStore.load() handles agent with no existing MCP config."""
        # Create a valid MCP config file
        json_config = {
            "mcpServers": {
                "fetch": {
                    "command": "uvx",
                    "args": ["mcp-server-fetch"]
                }
            }
        }

        store = _make_store(tmp_path)

        # Create mcp config file directly
        _write_mcp_config_file(store, json_config)

        agent = Agent(
            llm=LLM(model='test-model', api_key='test-key', service_id='test-service'),
            tools=[],
            mcp_config={}
        )

        store.save(agent)
        agent = store.load()

        combined_mcp_config = agent.mcp_config['mcpServers']

        # Should contain the new server from JSON file
        assert 'fetch' in combined_mcp_config
        assert combined_mcp_config['fetch']['command'] == 'uvx'
        assert combined_mcp_config['fetch']['args'] == ['mcp-server-fetch']

        # Should not contain any other servers
        assert len(combined_mcp_config) == 1
