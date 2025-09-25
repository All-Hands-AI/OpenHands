"""Tests for MCP configuration validation and agent store functionality."""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from openhands_cli.locations import AGENT_SETTINGS_PATH, MCP_CONFIG_PATH
import pytest
from prompt_toolkit.validation import ValidationError

from openhands_cli.tui.settings.store import AgentStore
from openhands_cli.user_actions.mcp_action import MCPConfigValidator
from openhands.sdk import LocalFileStore, Agent, LLM

class TestMCPConfigValidator:
    """Test the MCPConfigValidator functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.validator = MCPConfigValidator()

    @pytest.mark.parametrize("text", [
    (""),
    ("   \t\n   "),
    ])
    def test_validator_rejects_emptyish(self, text):
        doc = MagicMock()
        doc.text = text
        with pytest.raises(ValidationError) as exc:
            MCPConfigValidator().validate(doc)
        assert "Path for MCP config cannot be empty" in str(exc.value)


    def test_validator_rejects_nonexistent_file(self):
        """Test that validator rejects non-existent file path."""
        document = MagicMock()
        document.text = "/path/that/does/not/exist.json"

        with pytest.raises(ValidationError) as exc_info:
            self.validator.validate(document)

        # The actual error message from fastmcp for non-existent files
        error_msg = str(exc_info.value)
        assert "No MCP servers defined in the config" in error_msg

    def test_validator_rejects_directory_path(self, tmp_path):
        """Test that validator rejects directory path instead of file."""
        document = MagicMock()
        document.text = str(tmp_path)
        with pytest.raises(ValidationError) as exc_info:
            self.validator.validate(document)
        assert "Is a directory" in str(exc_info.value)

    def test_validator_rejects_non_json_file(self, tmp_path):
        p = tmp_path / "not_json.txt"
        p.write_text("This is not JSON content")

        document = MagicMock()
        document.text = str(p)

        with pytest.raises(ValidationError) as exc:
            MCPConfigValidator().validate(document)

        assert "Invalid JSON" in str(exc.value)


    def test_validator_rejects_invalid_json_format(self, tmp_path):
        """Test that validator rejects invalid JSON format."""
        p = tmp_path / "bad_mcp.json"
        p.write_text(json.dumps({"mcpServers": {"server1": "not_a_dict"}}))
        document = MagicMock()
        document.text = str(p)
        with pytest.raises(ValidationError) as exc_info:
            self.validator.validate(document)
        assert "validation error" in str(exc_info.value).lower()

    def test_validator_rejects_invalid_mcp_config_format(self, tmp_path):
        """Test that validator rejects JSON with invalid server configurations."""
        # Test with invalid server configuration that should cause validation errors
        p = tmp_path / "bad_mcp.json"
        p.write_text(json.dumps({"mcpServers": {"server1": "not_a_dict"}}))
        document = MagicMock()
        document.text = str(p)
        with pytest.raises(ValidationError) as exc_info:
            self.validator.validate(document)
        assert "validation error" in str(exc_info.value).lower()

    def test_validator_accepts_valid_mcp_config(self, tmp_path):
        """Test that validator accepts valid MCP configuration."""
        p = tmp_path / "ok_mcp.json"
        p.write_text(json.dumps({
            "mcpServers": {
                "fetch": {"command": "uvx", "args": ["mcp-server-fetch"]},
                "notion": {"url": "https://mcp.notion.com/mcp", "auth": "oauth"},
            }
        }))
        document = MagicMock()
        document.text = str(p)
        # should not raise
        self.validator.validate(document)



def _make_store(tmp_path: Path) -> AgentStore:
    store = AgentStore()
    store.file_store = LocalFileStore(root=str(tmp_path))
    return store


def _write_agent_settings(store: AgentStore, agent: Agent) -> None:
    store.save(agent)

def _write_mcp_config_pointer(store: AgentStore, path: str) -> None:
    store.file_store.write(MCP_CONFIG_PATH, path)

class TestAgentStoreMCPConfiguration:
    """Test the AgentStore MCP configuration loading functionality."""


    def test_load_mcp_configuration_file_not_found(self, tmp_path):
        """
        No MCP_CONFIG_PATH file present under store root.
        Should return {}.
        """
        store = _make_store(tmp_path)
        assert store.load_mcp_configuration() == {}

    def test_load_mcp_configuration_path_not_exist(self, tmp_path):
        """
        MCP_CONFIG_PATH file points to a non-existent absolute path.
        Should return {}.
        """
        store = _make_store(tmp_path)
        _write_mcp_config_pointer(store, 'does_not_exist.json')
        assert store.load_mcp_configuration() == {}


    def test_load_mcp_configuration_corrupted_file(self, tmp_path):
        store = _make_store(tmp_path)
        mcp_json_file_path = tmp_path / 'invalid.json'
        _write_mcp_config_pointer(store, str(mcp_json_file_path))
        mcp_json_file_path.write_text('{"invalid": json content}')  # invalid JSON
        assert store.load_mcp_configuration() == {}


    def test_load_mcp_configuration_invalid_format(self, tmp_path):
        """Test that load_mcp_configuration handles invalid MCP config format."""
        store = _make_store(tmp_path)
        mcp_json_file_path = tmp_path / 'invalid_format.json'
        with open(mcp_json_file_path, 'w') as f:
            json.dump({"someOtherKey": "value"}, f)  # Missing mcpServers

        _write_mcp_config_pointer(store, str(mcp_json_file_path))
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

        mcp_json_file_name = tmp_path / 'valid.json'
        with open(mcp_json_file_name, 'w') as f:
            json.dump(valid_config, f)

        _write_mcp_config_pointer(store, str(mcp_json_file_name))

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

        # Create mcp config
        mcp_json_file_name = tmp_path / 'mcp_config.json'
        with open(mcp_json_file_name, 'w') as f:
            json.dump(json_config, f)

        # Save pointer to mcp config
        _write_mcp_config_pointer(store, str(mcp_json_file_name))

        # Save agent with existing mcp servers
        agent = Agent(
            llm=LLM(model="test-model", api_key="test-key"),
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

        # Create mcp config
        mcp_json_file_name = tmp_path / 'mcp_config.json'
        with open(mcp_json_file_name, 'w') as f:
            json.dump(json_config, f)

        _write_mcp_config_pointer(store, str(mcp_json_file_name))

        agent = Agent(
            llm=LLM(model='test-model', api_key='test-key'),
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
