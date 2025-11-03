"""Unit tests for MCP settings reconciliation between persistent agent and mcp.json file."""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from pydantic import SecretStr

from openhands_cli.tui.settings.store import AgentStore
from openhands_cli.locations import MCP_CONFIG_FILE, AGENT_SETTINGS_PATH
from openhands.sdk import Agent, LLM
from openhands.sdk.context.condenser import LLMSummarizingCondenser


@pytest.fixture
def temp_persistence_dir(tmp_path, monkeypatch):
    """Create a temporary persistence directory and patch the locations."""
    persistence_dir = tmp_path / "openhands"
    persistence_dir.mkdir()
    
    # Patch the PERSISTENCE_DIR in the store module
    monkeypatch.setattr(
        'openhands_cli.tui.settings.store.PERSISTENCE_DIR',
        str(persistence_dir)
    )
    
    return persistence_dir


@pytest.fixture
def sample_agent():
    """Create a sample agent with MCP configuration."""
    return Agent(
        llm=LLM(
            model='gpt-4',
            api_key=SecretStr('test-key'),
            usage_id='test-service'
        ),
        tools=[],
        mcp_config={
            'mcpServers': {
                'persistent_server': {
                    'command': 'python',
                    'args': ['-m', 'persistent_server'],
                    'env': {'TEST': 'value'}
                }
            }
        }
    )


@pytest.fixture
def agent_store():
    """Create an AgentStore instance."""
    return AgentStore()


def create_mcp_json_file(persistence_dir: Path, mcp_config: dict):
    """Helper to create mcp.json file with given configuration."""
    mcp_file = persistence_dir / MCP_CONFIG_FILE
    mcp_file.write_text(json.dumps(mcp_config))


def create_agent_settings_file(persistence_dir: Path, agent: Agent):
    """Helper to create agent_settings.json file."""
    agent_file = persistence_dir / AGENT_SETTINGS_PATH
    agent_file.write_text(agent.model_dump_json(context={'expose_secrets': True}))


class TestMCPSettingsReconciliation:
    """Test cases for MCP settings reconciliation behavior."""

    def test_load_mcp_configuration_with_valid_file(self, temp_persistence_dir, agent_store):
        """Test loading MCP configuration from a valid mcp.json file."""
        # Arrange
        mcp_config = {
            'mcpServers': {
                'file_server': {
                    'command': 'uvx',
                    'args': ['mcp-server-fetch']
                },
                'notion_server': {
                    'url': 'https://mcp.notion.com/mcp',
                    'auth': 'oauth'
                }
            }
        }
        create_mcp_json_file(temp_persistence_dir, mcp_config)
        
        # Act
        result = agent_store.load_mcp_configuration()
        
        # Assert - fastmcp adds default values like env and transport
        expected = {
            'file_server': {
                'command': 'uvx',
                'args': ['mcp-server-fetch'],
                'env': {},
                'transport': 'stdio'
            },
            'notion_server': {
                'url': 'https://mcp.notion.com/mcp',
                'auth': 'oauth',
                'headers': {}  # URL-based servers get headers instead of env
            }
        }
        assert result == expected

    def test_load_mcp_configuration_with_missing_file(self, temp_persistence_dir, agent_store):
        """Test loading MCP configuration when mcp.json file doesn't exist."""
        # Act (no mcp.json file created)
        result = agent_store.load_mcp_configuration()
        
        # Assert
        assert result == {}

    def test_load_mcp_configuration_with_invalid_json(self, temp_persistence_dir, agent_store):
        """Test loading MCP configuration from invalid JSON file."""
        # Arrange
        mcp_file = temp_persistence_dir / MCP_CONFIG_FILE
        mcp_file.write_text('{"invalid": json content}')  # Invalid JSON
        
        # Act
        result = agent_store.load_mcp_configuration()
        
        # Assert
        assert result == {}

    def test_load_mcp_configuration_with_missing_mcpservers_key(self, temp_persistence_dir, agent_store):
        """Test loading MCP configuration when file exists but lacks mcpServers key."""
        # Arrange
        mcp_config = {
            'otherConfig': 'value'
            # Missing 'mcpServers' key
        }
        create_mcp_json_file(temp_persistence_dir, mcp_config)
        
        # Act
        result = agent_store.load_mcp_configuration()
        
        # Assert - should handle KeyError gracefully
        assert result == {}

    @patch('openhands_cli.tui.settings.store.get_llm_metadata')
    @patch('openhands_cli.tui.settings.store.get_default_tools')
    def test_load_agent_uses_only_mcp_json_config(
        self, 
        mock_get_tools, 
        mock_get_metadata,
        temp_persistence_dir, 
        sample_agent, 
        agent_store
    ):
        """Test that load() uses only mcp.json config, ignoring persistent agent's MCP config."""
        # Arrange
        mock_get_tools.return_value = []
        mock_get_metadata.return_value = {}
        
        # Create agent with existing MCP config
        create_agent_settings_file(temp_persistence_dir, sample_agent)
        
        # Create mcp.json with different servers
        mcp_config = {
            'mcpServers': {
                'file_server': {
                    'command': 'uvx',
                    'args': ['mcp-server-fetch']
                }
            }
        }
        create_mcp_json_file(temp_persistence_dir, mcp_config)
        
        # Act
        loaded_agent = agent_store.load()
        
        # Assert
        assert loaded_agent is not None
        assert loaded_agent.mcp_config == {
            'mcpServers': {
                'file_server': {
                    'command': 'uvx',
                    'args': ['mcp-server-fetch'],
                    'env': {},
                    'transport': 'stdio'
                }
            }
        }
        # The persistent agent's 'persistent_server' should be completely ignored

    @patch('openhands_cli.tui.settings.store.get_llm_metadata')
    @patch('openhands_cli.tui.settings.store.get_default_tools')
    def test_load_agent_with_no_mcp_json_file(
        self, 
        mock_get_tools, 
        mock_get_metadata,
        temp_persistence_dir, 
        sample_agent, 
        agent_store
    ):
        """Test that load() uses empty MCP config when no mcp.json file exists."""
        # Arrange
        mock_get_tools.return_value = []
        mock_get_metadata.return_value = {}
        
        # Create agent with existing MCP config
        create_agent_settings_file(temp_persistence_dir, sample_agent)
        
        # No mcp.json file created
        
        # Act
        loaded_agent = agent_store.load()
        
        # Assert
        assert loaded_agent is not None
        assert loaded_agent.mcp_config == {}
        # The persistent agent's MCP config should be completely ignored

    @patch('openhands_cli.tui.settings.store.get_llm_metadata')
    @patch('openhands_cli.tui.settings.store.get_default_tools')
    def test_load_agent_with_empty_mcp_json_mcpservers(
        self, 
        mock_get_tools, 
        mock_get_metadata,
        temp_persistence_dir, 
        sample_agent, 
        agent_store
    ):
        """Test that load() handles empty mcpServers in mcp.json correctly."""
        # Arrange
        mock_get_tools.return_value = []
        mock_get_metadata.return_value = {}
        
        # Create agent with existing MCP config
        create_agent_settings_file(temp_persistence_dir, sample_agent)
        
        # Create mcp.json with empty mcpServers
        mcp_config = {
            'mcpServers': {}
        }
        create_mcp_json_file(temp_persistence_dir, mcp_config)
        
        # Act
        loaded_agent = agent_store.load()
        
        # Assert
        assert loaded_agent is not None
        assert loaded_agent.mcp_config == {}

    @patch('openhands_cli.tui.settings.store.get_llm_metadata')
    @patch('openhands_cli.tui.settings.store.get_default_tools')
    def test_load_agent_with_condenser_and_mcp_config(
        self, 
        mock_get_tools, 
        mock_get_metadata,
        temp_persistence_dir, 
        agent_store
    ):
        """Test that load() works correctly with agents that have condensers."""
        # Arrange
        mock_get_tools.return_value = []
        mock_get_metadata.return_value = {}
        
        # Create agent with condenser and MCP config
        condenser_llm = LLM(
            model='gpt-3.5-turbo',
            api_key=SecretStr('condenser-key'),
            usage_id='condenser-service'
        )
        agent_with_condenser = Agent(
            llm=LLM(
                model='gpt-4',
                api_key=SecretStr('test-key'),
                usage_id='test-service'
            ),
            tools=[],
            mcp_config={
                'mcpServers': {
                    'persistent_server': {
                        'command': 'python',
                        'args': ['-m', 'persistent_server']
                    }
                }
            },
            condenser=LLMSummarizingCondenser(llm=condenser_llm)
        )
        
        create_agent_settings_file(temp_persistence_dir, agent_with_condenser)
        
        # Create mcp.json with different servers
        mcp_config = {
            'mcpServers': {
                'file_server': {
                    'command': 'uvx',
                    'args': ['mcp-server-fetch']
                }
            }
        }
        create_mcp_json_file(temp_persistence_dir, mcp_config)
        
        # Act
        loaded_agent = agent_store.load()
        
        # Assert
        assert loaded_agent is not None
        assert loaded_agent.mcp_config == {
            'mcpServers': {
                'file_server': {
                    'command': 'uvx',
                    'args': ['mcp-server-fetch'],
                    'env': {},
                    'transport': 'stdio'
                }
            }
        }
        assert loaded_agent.condenser is not None

    def test_behavioral_change_documentation(self, temp_persistence_dir, agent_store):
        """Test documenting the key behavioral change in MCP settings reconciliation.
        
        This test documents the change from merging agent + file configs 
        to using only file config.
        """
        # This test serves as documentation of the behavioral change:
        # OLD BEHAVIOR: agent.mcp_config.update(file_config)
        # NEW BEHAVIOR: use only file_config, ignore agent.mcp_config
        
        # Arrange - simulate the old vs new behavior
        agent_mcp_config = {
            'persistent_server': {
                'command': 'python',
                'args': ['-m', 'persistent_server']
            }
        }
        
        file_mcp_config = {
            'file_server': {
                'command': 'uvx',
                'args': ['mcp-server-fetch']
            }
        }
        
        create_mcp_json_file(temp_persistence_dir, {'mcpServers': file_mcp_config})
        
        # Act
        result = agent_store.load_mcp_configuration()
        
        # Assert - NEW BEHAVIOR: only file config is used (with fastmcp defaults)
        expected_with_defaults = {
            'file_server': {
                'command': 'uvx',
                'args': ['mcp-server-fetch'],
                'env': {},
                'transport': 'stdio'
            }
        }
        assert result == expected_with_defaults
        assert 'persistent_server' not in result  # Agent config is ignored
        assert 'file_server' in result  # File config is used
        
        # OLD BEHAVIOR would have been:
        # merged_config = agent_mcp_config.copy()
        # merged_config.update(file_mcp_config)
        # This would result in both 'persistent_server' and 'file_server'


class TestMCPConfigurationEdgeCases:
    """Test edge cases and error conditions for MCP configuration loading."""

    def test_load_mcp_configuration_with_nested_structure(self, temp_persistence_dir, agent_store):
        """Test loading MCP configuration with complex nested structure."""
        # Arrange
        mcp_config = {
            'mcpServers': {
                'complex_server': {
                    'command': 'python',
                    'args': ['-m', 'server'],
                    'env': {
                        'API_KEY': 'secret',
                        'DEBUG': 'true'
                    },
                    'transport': 'stdio',
                    'timeout': 30
                }
            },
            'otherConfig': {
                'setting': 'value'
            }
        }
        create_mcp_json_file(temp_persistence_dir, mcp_config)
        
        # Act
        result = agent_store.load_mcp_configuration()
        
        # Assert
        expected = {
            'complex_server': {
                'command': 'python',
                'args': ['-m', 'server'],
                'env': {
                    'API_KEY': 'secret',
                    'DEBUG': 'true'
                },
                'transport': 'stdio',
                'timeout': 30
            }
        }
        assert result == expected

    def test_load_mcp_configuration_with_permission_error(self, temp_persistence_dir, agent_store):
        """Test loading MCP configuration when file exists but can't be read."""
        # Arrange
        mcp_file = temp_persistence_dir / MCP_CONFIG_FILE
        mcp_file.write_text('{"mcpServers": {}}')
        
        # Mock file read to raise PermissionError
        with patch('pathlib.Path.read_text', side_effect=PermissionError("Permission denied")):
            # Act
            result = agent_store.load_mcp_configuration()
            
            # Assert
            assert result == {}

    def test_load_mcp_configuration_with_unicode_content(self, temp_persistence_dir, agent_store):
        """Test loading MCP configuration with Unicode characters."""
        # Arrange
        mcp_config = {
            'mcpServers': {
                'unicode_server': {
                    'command': 'python',
                    'args': ['-m', 'server_with_émojis_🚀'],
                    'description': 'Server with Unicode: café, naïve, résumé'
                }
            }
        }
        create_mcp_json_file(temp_persistence_dir, mcp_config)
        
        # Act
        result = agent_store.load_mcp_configuration()
        
        # Assert
        expected = {
            'unicode_server': {
                'command': 'python',
                'args': ['-m', 'server_with_émojis_🚀'],
                'description': 'Server with Unicode: café, naïve, résumé',
                'env': {},
                'transport': 'stdio'
            }
        }
        assert result == expected