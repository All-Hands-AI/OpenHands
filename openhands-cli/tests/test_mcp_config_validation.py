"""Tests for MCP configuration validation and agent store functionality."""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from prompt_toolkit.validation import ValidationError

from openhands_cli.tui.settings.store import AgentStore
from openhands_cli.user_actions.mcp_action import MCPConfigValidator


class TestMCPConfigValidator:
    """Test the MCPConfigValidator functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.validator = MCPConfigValidator()

    def test_validator_rejects_empty_path(self):
        """Test that validator rejects empty path."""
        document = MagicMock()
        document.text = ""
        
        with pytest.raises(ValidationError) as exc_info:
            self.validator.validate(document)
        
        assert "Path for MCP config cannot be empty" in str(exc_info.value)

    def test_validator_rejects_whitespace_only_path(self):
        """Test that validator rejects whitespace-only path."""
        document = MagicMock()
        document.text = "   \t\n   "
        
        with pytest.raises(ValidationError) as exc_info:
            self.validator.validate(document)
        
        # The actual error message from fastmcp for whitespace paths
        assert "No MCP servers defined in the config" in str(exc_info.value)

    def test_validator_rejects_nonexistent_file(self):
        """Test that validator rejects non-existent file path."""
        document = MagicMock()
        document.text = "/path/that/does/not/exist.json"
        
        with pytest.raises(ValidationError) as exc_info:
            self.validator.validate(document)
        
        # The actual error message from fastmcp for non-existent files
        error_msg = str(exc_info.value)
        assert "No MCP servers defined in the config" in error_msg

    def test_validator_rejects_directory_path(self):
        """Test that validator rejects directory path instead of file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            document = MagicMock()
            document.text = temp_dir
            
            with pytest.raises(ValidationError) as exc_info:
                self.validator.validate(document)
            
            # Should get an IsADirectoryError from fastmcp
            error_msg = str(exc_info.value)
            assert "Is a directory" in error_msg

    def test_validator_rejects_non_json_file(self):
        """Test that validator rejects non-JSON file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
            temp_file.write("This is not JSON content")
            temp_file.flush()
            
            try:
                document = MagicMock()
                document.text = temp_file.name
                
                with pytest.raises(ValidationError) as exc_info:
                    self.validator.validate(document)
                
                error_msg = str(exc_info.value)
                assert "Invalid JSON" in error_msg
            finally:
                os.unlink(temp_file.name)

    def test_validator_rejects_invalid_json_format(self):
        """Test that validator rejects invalid JSON format."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
            temp_file.write('{"invalid": json content}')  # Invalid JSON
            temp_file.flush()
            
            try:
                document = MagicMock()
                document.text = temp_file.name
                
                with pytest.raises(ValidationError) as exc_info:
                    self.validator.validate(document)
                
                error_msg = str(exc_info.value)
                assert "Invalid JSON" in error_msg
            finally:
                os.unlink(temp_file.name)

    def test_validator_rejects_invalid_mcp_config_format(self):
        """Test that validator rejects JSON with invalid server configurations."""
        # Test with invalid server configuration that should cause validation errors
        invalid_config = {
            "mcpServers": {
                "server1": "not_a_dict"  # Should be a dict, not string
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
            json.dump(invalid_config, temp_file)
            temp_file.flush()
            
            try:
                document = MagicMock()
                document.text = temp_file.name
                
                with pytest.raises(ValidationError) as exc_info:
                    self.validator.validate(document)
                
                error_msg = str(exc_info.value)
                # Should get a validation error about the configuration format
                assert "validation error" in error_msg.lower()
            finally:
                os.unlink(temp_file.name)

    def test_validator_accepts_valid_mcp_config(self):
        """Test that validator accepts valid MCP configuration."""
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
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
            json.dump(valid_config, temp_file)
            temp_file.flush()
            
            try:
                document = MagicMock()
                document.text = temp_file.name
                
                # Should not raise any exception
                self.validator.validate(document)
            finally:
                os.unlink(temp_file.name)


class TestAgentStoreMCPConfiguration:
    """Test the AgentStore MCP configuration loading functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.agent_store = AgentStore()
        
        # Mock the file store to use our temp directory
        self.mock_file_store = MagicMock()
        self.agent_store.file_store = self.mock_file_store

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_load_mcp_configuration_file_not_found(self):
        """Test that load_mcp_configuration handles missing config file."""
        # Mock file store to raise FileNotFoundError
        self.mock_file_store.read.side_effect = FileNotFoundError("Config file not found")
        
        result = self.agent_store.load_mcp_configuration()
        
        # Should return empty dict when config file doesn't exist
        assert result == {}

    def test_load_mcp_configuration_path_not_exist(self):
        """Test that load_mcp_configuration handles non-existent path in config."""
        # Mock file store to return a path that doesn't exist
        nonexistent_path = "/path/that/does/not/exist.json"
        self.mock_file_store.read.return_value = nonexistent_path
        
        result = self.agent_store.load_mcp_configuration()
        
        # Should return empty dict when the path in config doesn't exist
        assert result == {}

    def test_load_mcp_configuration_corrupted_file(self):
        """Test that load_mcp_configuration handles corrupted MCP config file with warning."""
        # Create a corrupted JSON file
        corrupted_file = os.path.join(self.temp_dir, "corrupted.json")
        with open(corrupted_file, 'w') as f:
            f.write('{"invalid": json content}')  # Invalid JSON
        
        # Mock file store to return the corrupted file path
        self.mock_file_store.read.return_value = corrupted_file
        
        # Should return empty dict and not raise exception
        result = self.agent_store.load_mcp_configuration()
        assert result == {}

    def test_load_mcp_configuration_invalid_format(self):
        """Test that load_mcp_configuration handles invalid MCP config format."""
        # Create a valid JSON file but with invalid MCP format
        invalid_config_file = os.path.join(self.temp_dir, "invalid_format.json")
        with open(invalid_config_file, 'w') as f:
            json.dump({"someOtherKey": "value"}, f)  # Missing mcpServers
        
        # Mock file store to return the invalid config file path
        self.mock_file_store.read.return_value = invalid_config_file
        
        # Should return empty dict when config format is invalid
        result = self.agent_store.load_mcp_configuration()
        assert result == {}

    def test_load_mcp_configuration_valid_config(self):
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
        
        valid_config_file = os.path.join(self.temp_dir, "valid_config.json")
        with open(valid_config_file, 'w') as f:
            json.dump(valid_config, f)
        
        # Mock file store to return the valid config file path
        self.mock_file_store.read.return_value = valid_config_file
        
        result = self.agent_store.load_mcp_configuration()
        
        # Should return the mcpServers section with additional fields added by fastmcp
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

    @patch('openhands_cli.tui.settings.store.print_formatted_text')
    def test_agent_store_load_combines_mcp_configs(self, mock_print):
        """Test that AgentStore.load() combines existing MCP servers with new ones from JSON file."""
        # Create a valid MCP config file
        json_config = {
            "mcpServers": {
                "fetch": {
                    "command": "uvx",
                    "args": ["mcp-server-fetch"]
                }
            }
        }
        
        json_config_file = os.path.join(self.temp_dir, "mcp_config.json")
        with open(json_config_file, 'w') as f:
            json.dump(json_config, f)
        
        # Mock the file store to return both agent settings and MCP config path
        def mock_read(path):
            if "agent_settings.json" in path:
                # Return a mock agent with existing MCP config
                mock_agent_data = {
                    "llm": {"model": "test-model", "api_key": "test-key"},
                    "tools": [],
                    "mcp_config": {
                        "mcpServers": {
                            "existing_server": {
                                "url": "https://existing.com/mcp",
                                "auth": "none"
                            }
                        }
                    }
                }
                return json.dumps(mock_agent_data)
            elif "mcp_config_path.txt" in path:
                return json_config_file
            else:
                raise FileNotFoundError(f"File not found: {path}")
        
        self.mock_file_store.read.side_effect = mock_read
        
        # Mock the Agent class and get_default_tools
        with patch('openhands_cli.tui.settings.store.Agent') as mock_agent_class, \
             patch('openhands_cli.tui.settings.store.get_default_tools') as mock_get_tools:
            
            # Create a mock agent instance
            mock_agent = MagicMock()
            mock_agent.mcp_config = {
                "mcpServers": {
                    "existing_server": {
                        "url": "https://existing.com/mcp",
                        "auth": "none"
                    }
                }
            }
            mock_agent.model_copy.return_value = mock_agent
            
            # Mock the Agent.model_validate_json to return our mock agent
            mock_agent_class.model_validate_json.return_value = mock_agent
            
            # Mock get_default_tools
            mock_get_tools.return_value = []
            
            # Load the agent
            result = self.agent_store.load()
            
            # Verify that model_copy was called with combined MCP config
            mock_agent.model_copy.assert_called_once()
            call_args = mock_agent.model_copy.call_args[1]['update']
            
            # Check that the MCP config contains both existing and new servers
            combined_mcp_config = call_args['mcp_config']['mcpServers']
            
            # Should contain the new server from JSON file
            assert 'fetch' in combined_mcp_config
            assert combined_mcp_config['fetch']['command'] == 'uvx'
            assert combined_mcp_config['fetch']['args'] == ['mcp-server-fetch']
            
            # Should also contain the existing server from agent
            assert 'existing_server' in combined_mcp_config
            assert combined_mcp_config['existing_server']['url'] == 'https://existing.com/mcp'

    def test_agent_store_load_handles_missing_agent_file(self):
        """Test that AgentStore.load() handles missing agent settings file."""
        # Mock file store to raise FileNotFoundError for agent settings
        self.mock_file_store.read.side_effect = FileNotFoundError("Agent settings not found")
        
        result = self.agent_store.load()
        
        # Should return None when agent settings file doesn't exist
        assert result is None

    @patch('openhands_cli.tui.settings.store.print_formatted_text')
    def test_agent_store_load_handles_corrupted_agent_file(self, mock_print):
        """Test that AgentStore.load() handles corrupted agent settings file."""
        # Mock file store to return invalid JSON for agent settings
        self.mock_file_store.read.return_value = '{"invalid": json content}'
        
        result = self.agent_store.load()
        
        # Should return None and print error message when agent file is corrupted
        assert result is None
        mock_print.assert_called_once()
        # Check that the error message was printed
        call_args = mock_print.call_args[0][0]
        assert "corrupted" in str(call_args).lower()

    def test_agent_store_load_handles_no_mcp_config_in_agent(self):
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
        
        json_config_file = os.path.join(self.temp_dir, "mcp_config.json")
        with open(json_config_file, 'w') as f:
            json.dump(json_config, f)
        
        # Mock the file store
        def mock_read(path):
            if "agent_settings.json" in path:
                # Return a mock agent without MCP config
                mock_agent_data = {
                    "llm": {"model": "test-model", "api_key": "test-key"},
                    "tools": [],
                    "mcp_config": {}  # Empty MCP config
                }
                return json.dumps(mock_agent_data)
            elif "mcp_config_path.txt" in path:
                return json_config_file
            else:
                raise FileNotFoundError(f"File not found: {path}")
        
        self.mock_file_store.read.side_effect = mock_read
        
        # Mock the Agent class and get_default_tools
        with patch('openhands_cli.tui.settings.store.Agent') as mock_agent_class, \
             patch('openhands_cli.tui.settings.store.get_default_tools') as mock_get_tools:
            
            # Create a mock agent instance
            mock_agent = MagicMock()
            mock_agent.mcp_config = {}  # No existing MCP config
            mock_agent.model_copy.return_value = mock_agent
            
            # Mock the Agent.model_validate_json to return our mock agent
            mock_agent_class.model_validate_json.return_value = mock_agent
            
            # Mock get_default_tools
            mock_get_tools.return_value = []
            
            # Load the agent
            result = self.agent_store.load()
            
            # Verify that model_copy was called with MCP config from JSON file only
            mock_agent.model_copy.assert_called_once()
            call_args = mock_agent.model_copy.call_args[1]['update']
            
            # Check that the MCP config contains only the new server from JSON file
            combined_mcp_config = call_args['mcp_config']['mcpServers']
            
            # Should contain the new server from JSON file
            assert 'fetch' in combined_mcp_config
            assert combined_mcp_config['fetch']['command'] == 'uvx'
            assert combined_mcp_config['fetch']['args'] == ['mcp-server-fetch']
            
            # Should not contain any other servers
            assert len(combined_mcp_config) == 1