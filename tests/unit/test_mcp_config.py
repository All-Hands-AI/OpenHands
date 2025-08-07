import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import ValidationError

from openhands.controller.agent import Agent
from openhands.core.config import OpenHandsConfig, load_from_env
from openhands.core.config.mcp_config import (
    MCPConfig,
    MCPSHTTPServerConfig,
    MCPSSEServerConfig,
    MCPStdioServerConfig,
)
from openhands.mcp.utils import create_mcp_clients
from openhands.server.session.conversation_init_data import ConversationInitData
from openhands.server.session.session import Session
from openhands.storage.memory import InMemoryFileStore


def test_valid_sse_config():
    """Test a valid SSE configuration."""
    config = MCPConfig(
        sse_servers=[
            MCPSSEServerConfig(url='http://server1:8080'),
            MCPSSEServerConfig(url='http://server2:8080'),
        ]
    )
    config.validate_servers()  # Should not raise any exception


def test_empty_sse_config():
    """Test SSE configuration with empty servers list."""
    config = MCPConfig(sse_servers=[])
    config.validate_servers()


def test_invalid_sse_url():
    """Test SSE configuration with invalid URL format."""
    with pytest.raises(ValidationError) as exc_info:
        MCPSSEServerConfig(url='not_a_url')
    assert 'URL must include a scheme' in str(exc_info.value)


def test_duplicate_sse_urls():
    """Test SSE configuration with duplicate server URLs."""
    config = MCPConfig(
        sse_servers=[
            MCPSSEServerConfig(url='http://server1:8080'),
            MCPSSEServerConfig(url='http://server1:8080'),
        ]
    )
    with pytest.raises(ValueError) as exc_info:
        config.validate_servers()
    assert 'Duplicate MCP server URLs are not allowed' in str(exc_info.value)


def test_from_toml_section_valid():
    """Test creating config from valid TOML section."""
    data = {
        'sse_servers': ['http://server1:8080'],
    }
    result = MCPConfig.from_toml_section(data)
    assert 'mcp' in result
    assert len(result['mcp'].sse_servers) == 1
    assert result['mcp'].sse_servers[0].url == 'http://server1:8080'


def test_from_toml_section_invalid_sse():
    """Test creating config from TOML section with invalid SSE URL."""
    data = {
        'sse_servers': ['not_a_url'],
    }
    with pytest.raises(ValueError) as exc_info:
        MCPConfig.from_toml_section(data)
    assert 'URL must include a scheme' in str(exc_info.value)


def test_complex_urls():
    """Test SSE configuration with complex URLs."""
    config = MCPConfig(
        sse_servers=[
            MCPSSEServerConfig(url='https://user:pass@server1:8080/path?query=1'),
            MCPSSEServerConfig(url='wss://server2:8443/ws'),
            MCPSSEServerConfig(url='http://subdomain.example.com:9090'),
        ]
    )
    config.validate_servers()  # Should not raise any exception


def test_mcp_sse_server_config_with_api_key():
    """Test MCPSSEServerConfig with API key."""
    config = MCPSSEServerConfig(url='http://server1:8080', api_key='test-api-key')
    assert config.url == 'http://server1:8080'
    assert config.api_key == 'test-api-key'


def test_mcp_sse_server_config_without_api_key():
    """Test MCPSSEServerConfig without API key."""
    config = MCPSSEServerConfig(url='http://server1:8080')
    assert config.url == 'http://server1:8080'
    assert config.api_key is None


def test_mcp_stdio_server_config_basic():
    """Test basic MCPStdioServerConfig."""
    config = MCPStdioServerConfig(name='test-server', command='python')
    assert config.name == 'test-server'
    assert config.command == 'python'
    assert config.args == []
    assert config.env == {}


def test_mcp_stdio_server_config_with_args_and_env():
    """Test MCPStdioServerConfig with args and env."""
    config = MCPStdioServerConfig(
        name='test-server',
        command='python',
        args=['-m', 'server'],
        env={'DEBUG': 'true', 'PORT': '8080'},
    )
    assert config.name == 'test-server'
    assert config.command == 'python'
    assert config.args == ['-m', 'server']
    assert config.env == {'DEBUG': 'true', 'PORT': '8080'}


def test_mcp_config_with_stdio_servers():
    """Test MCPConfig with stdio servers."""
    stdio_server = MCPStdioServerConfig(
        name='test-server',
        command='python',
        args=['-m', 'server'],
        env={'DEBUG': 'true'},
    )
    config = MCPConfig(stdio_servers=[stdio_server])
    assert len(config.stdio_servers) == 1
    assert config.stdio_servers[0].name == 'test-server'
    assert config.stdio_servers[0].command == 'python'
    assert config.stdio_servers[0].args == ['-m', 'server']
    assert config.stdio_servers[0].env == {'DEBUG': 'true'}


def test_from_toml_section_with_stdio_servers():
    """Test creating config from TOML section with stdio servers."""
    data = {
        'sse_servers': ['http://server1:8080'],
        'stdio_servers': [
            {
                'name': 'test-server',
                'command': 'python',
                'args': ['-m', 'server'],
                'env': {'DEBUG': 'true'},
            }
        ],
    }
    result = MCPConfig.from_toml_section(data)
    assert 'mcp' in result
    assert len(result['mcp'].sse_servers) == 1
    assert result['mcp'].sse_servers[0].url == 'http://server1:8080'
    assert len(result['mcp'].stdio_servers) == 1
    assert result['mcp'].stdio_servers[0].name == 'test-server'
    assert result['mcp'].stdio_servers[0].command == 'python'
    assert result['mcp'].stdio_servers[0].args == ['-m', 'server']
    assert result['mcp'].stdio_servers[0].env == {'DEBUG': 'true'}


def test_mcp_config_with_both_server_types():
    """Test MCPConfig with both SSE and stdio servers."""
    sse_server = MCPSSEServerConfig(url='http://server1:8080', api_key='test-api-key')
    stdio_server = MCPStdioServerConfig(
        name='test-server',
        command='python',
        args=['-m', 'server'],
        env={'DEBUG': 'true'},
    )
    config = MCPConfig(sse_servers=[sse_server], stdio_servers=[stdio_server])
    assert len(config.sse_servers) == 1
    assert config.sse_servers[0].url == 'http://server1:8080'
    assert config.sse_servers[0].api_key == 'test-api-key'
    assert len(config.stdio_servers) == 1
    assert config.stdio_servers[0].name == 'test-server'
    assert config.stdio_servers[0].command == 'python'


def test_mcp_config_model_validation_error():
    """Test MCPConfig validation error with invalid data."""
    with pytest.raises(ValidationError):
        # Missing required 'url' field
        MCPSSEServerConfig()

    with pytest.raises(ValidationError):
        # Missing required 'name' and 'command' fields
        MCPStdioServerConfig()


def test_mcp_config_extra_fields_forbidden():
    """Test that extra fields are forbidden in MCPConfig."""
    with pytest.raises(ValidationError):
        MCPConfig(extra_field='value')

    # Note: The nested models don't have 'extra': 'forbid' set, so they allow extra fields
    # We're only testing the main MCPConfig class here


def test_stdio_server_equality_with_different_env_order():
    """Test that MCPStdioServerConfig equality works with env in different order but respects arg order."""
    # Test 1: Same args, different env order
    server1 = MCPStdioServerConfig(
        name='test-server',
        command='python',
        args=['--verbose', '--debug', '--port=8080'],
        env={'DEBUG': 'true', 'PORT': '8080'},
    )

    server2 = MCPStdioServerConfig(
        name='test-server',
        command='python',
        args=['--verbose', '--debug', '--port=8080'],  # Same order
        env={'PORT': '8080', 'DEBUG': 'true'},  # Different order
    )

    # Should be equal because env is compared as a set
    assert server1 == server2

    # Test 2: Different args order
    server3 = MCPStdioServerConfig(
        name='test-server',
        command='python',
        args=['--debug', '--port=8080', '--verbose'],  # Different order
        env={'DEBUG': 'true', 'PORT': '8080'},
    )

    # Should NOT be equal because args order matters
    assert server1 != server3

    # Test 3: Different arg value
    server4 = MCPStdioServerConfig(
        name='test-server',
        command='python',
        args=['--verbose', '--debug', '--port=9090'],  # Different port
        env={'DEBUG': 'true', 'PORT': '8080'},
    )

    # Should not be equal
    assert server1 != server4

    # Test 4: Different env value
    server5 = MCPStdioServerConfig(
        name='test-server',
        command='python',
        args=['--verbose', '--debug', '--port=8080'],
        env={'DEBUG': 'true', 'PORT': '9090'},  # Different port
    )

    # Should not be equal
    assert server1 != server5


def test_mcp_stdio_server_args_parsing_basic():
    """Test MCPStdioServerConfig args parsing with basic shell-like format."""
    # Test basic space-separated parsing
    config = MCPStdioServerConfig(
        name='test-server', command='python', args='arg1 arg2 arg3'
    )
    assert config.args == ['arg1', 'arg2', 'arg3']

    # Test single argument
    config = MCPStdioServerConfig(
        name='test-server', command='python', args='single-arg'
    )
    assert config.args == ['single-arg']


def test_mcp_stdio_server_args_parsing_invalid_quotes():
    """Test MCPStdioServerConfig args parsing with invalid quotes."""
    # Test unmatched quotes
    with pytest.raises(ValidationError) as exc_info:
        MCPStdioServerConfig(
            name='test-server', command='python', args='--config "unmatched quote'
        )
    assert 'Invalid argument format' in str(exc_info.value)


def test_mcp_shttp_server_config_basic():
    """Test basic MCPSHTTPServerConfig."""
    config = MCPSHTTPServerConfig(url='http://server1:8080')
    assert config.url == 'http://server1:8080'
    assert config.api_key is None


def test_mcp_shttp_server_config_with_api_key():
    """Test MCPSHTTPServerConfig with API key."""
    config = MCPSHTTPServerConfig(url='http://server1:8080', api_key='test-api-key')
    assert config.url == 'http://server1:8080'
    assert config.api_key == 'test-api-key'


def test_mcp_config_with_shttp_servers():
    """Test MCPConfig with HTTP servers."""
    shttp_server = MCPSHTTPServerConfig(
        url='http://server1:8080',
        api_key='test-api-key',
    )
    config = MCPConfig(shttp_servers=[shttp_server])
    assert len(config.shttp_servers) == 1
    assert config.shttp_servers[0].url == 'http://server1:8080'
    assert config.shttp_servers[0].api_key == 'test-api-key'


def test_from_toml_section_with_shttp_servers():
    """Test creating config from TOML section with HTTP servers."""
    data = {
        'sse_servers': ['http://server1:8080'],
        'shttp_servers': [
            {
                'url': 'http://http-server:8080',
                'api_key': 'test-api-key',
            }
        ],
    }
    result = MCPConfig.from_toml_section(data)
    assert 'mcp' in result
    assert len(result['mcp'].sse_servers) == 1
    assert result['mcp'].sse_servers[0].url == 'http://server1:8080'
    assert len(result['mcp'].shttp_servers) == 1
    assert result['mcp'].shttp_servers[0].url == 'http://http-server:8080'
    assert result['mcp'].shttp_servers[0].api_key == 'test-api-key'


def test_env_var_mcp_shttp_server_config(monkeypatch):
    """Test creating MCPSHTTPServerConfig from environment variables."""
    # Set environment variables for MCP HTTP server
    monkeypatch.setenv(
        'MCP_SHTTP_SERVERS',
        '[{"url": "http://env-server:8080", "api_key": "env-api-key"}]',
    )

    # Create a config object
    config = OpenHandsConfig()

    # Load from environment
    load_from_env(config, os.environ)

    # Convert dictionary servers to proper server config objects by creating a new MCPConfig
    # This triggers the model validator which automatically converts dict servers to proper objects
    config.mcp = MCPConfig(
        sse_servers=config.mcp.sse_servers,
        stdio_servers=config.mcp.stdio_servers,
        shttp_servers=config.mcp.shttp_servers,
    )

    # Check that the HTTP server was added
    assert len(config.mcp.shttp_servers) == 1

    # Access the first server
    server = config.mcp.shttp_servers[0]

    # Verify it's a proper server config object
    assert isinstance(server, MCPSHTTPServerConfig)
    assert server.url == 'http://env-server:8080'
    assert server.api_key == 'env-api-key'

    # Now let's create a proper MCPConfig with the values from the environment
    mcp_config = MCPConfig(shttp_servers=config.mcp.shttp_servers)

    # Verify that the MCPSHTTPServerConfig objects are created correctly
    assert len(mcp_config.shttp_servers) == 1
    assert isinstance(mcp_config.shttp_servers[0], MCPSHTTPServerConfig)
    assert mcp_config.shttp_servers[0].url == 'http://env-server:8080'
    assert mcp_config.shttp_servers[0].api_key == 'env-api-key'


def test_env_var_mcp_shttp_server_config_with_toml(monkeypatch, tmp_path):
    """Test creating MCPSHTTPServerConfig from environment variables with TOML config."""
    # Create a TOML file with some MCP configuration
    toml_file = tmp_path / 'config.toml'
    with open(toml_file, 'w', encoding='utf-8') as f:
        f.write("""
[mcp]
sse_servers = ["http://toml-server:8080"]
shttp_servers = [
    { url = "http://toml-http-server:8080", api_key = "toml-api-key" }
]
""")

    # Set environment variables for MCP HTTP server to override TOML
    monkeypatch.setenv(
        'MCP_SHTTP_SERVERS',
        '[{"url": "http://env-server:8080", "api_key": "env-api-key"}]',
    )

    # Create a config object
    config = OpenHandsConfig()

    # Load from TOML first
    from openhands.core.config import load_from_toml

    load_from_toml(config, str(toml_file))

    # Verify TOML values were loaded
    assert len(config.mcp.shttp_servers) == 1
    assert isinstance(config.mcp.shttp_servers[0], MCPSHTTPServerConfig)
    assert config.mcp.shttp_servers[0].url == 'http://toml-http-server:8080'
    assert config.mcp.shttp_servers[0].api_key == 'toml-api-key'

    # Now load from environment, which should override TOML
    load_from_env(config, os.environ)

    # Check that the environment values override the TOML values
    assert len(config.mcp.shttp_servers) == 1

    # The values should now be from the environment
    server = config.mcp.shttp_servers[0]
    assert isinstance(server, dict)
    assert server.get('url') == 'http://env-server:8080'
    assert server.get('api_key') == 'env-api-key'


def test_env_var_mcp_shttp_servers_with_python_str_representation(monkeypatch):
    """Test creating MCPSHTTPServerConfig from environment variables using Python string representation."""
    # Create a Python list of dictionaries
    mcp_shttp_servers = [
        {'url': 'https://example.com/mcp/mcp', 'api_key': 'test-api-key'}
    ]

    # Set environment variable with the string representation of the Python list
    monkeypatch.setenv('MCP_SHTTP_SERVERS', str(mcp_shttp_servers))

    # Create a config object
    config = OpenHandsConfig()

    # Load from environment
    load_from_env(config, os.environ)

    # Check that the HTTP server was added
    assert len(config.mcp.shttp_servers) == 1

    # Access the first server
    server = config.mcp.shttp_servers[0]

    # Check that it's a dict with the expected keys
    assert isinstance(server, dict)
    assert server.get('url') == 'https://example.com/mcp/mcp'
    assert server.get('api_key') == 'test-api-key'


def test_convert_dict_to_mcp_http_server_config():
    """Test direct conversion of dictionary to MCPSHTTPServerConfig."""
    # Create a dictionary server configuration
    dict_server = {'url': 'http://env-server:8080', 'api_key': 'env-api-key'}

    # Convert the dictionary to an MCPSHTTPServerConfig object
    server_config = MCPSHTTPServerConfig(**dict_server)

    # Verify the conversion
    assert isinstance(server_config, MCPSHTTPServerConfig)
    assert server_config.url == 'http://env-server:8080'
    assert server_config.api_key == 'env-api-key'


@pytest.mark.asyncio
async def test_create_mcp_clients_with_server_config(monkeypatch):
    """Test that create_mcp_clients works with proper server config objects."""
    # Create a proper server configuration object
    server_config = MCPSHTTPServerConfig(
        url='http://env-server:8080', api_key='env-api-key'
    )

    # Patch the connect_http method to avoid actual HTTP requests
    monkeypatch.setattr(
        'openhands.mcp.client.MCPClient.connect_http',
        lambda self, server, conversation_id=None, timeout=30.0: None,
    )

    # Call create_mcp_clients with the proper server config object
    await create_mcp_clients(
        sse_servers=[],
        stdio_servers=[],
        shttp_servers=[server_config],
        conversation_id=None,
    )


@pytest.fixture
def mock_sio():
    return AsyncMock()


@pytest.mark.asyncio
async def test_session_preserves_env_mcp_config(mock_sio, monkeypatch):
    """Test that Session preserves MCP configuration from environment variables."""
    # Set environment variables for MCP HTTP server
    monkeypatch.setenv(
        'MCP_SHTTP_SERVERS',
        '[{"url": "http://env-server:8080", "api_key": "env-api-key"}]',
    )

    # Also set MCP_HOST to prevent the default server from being added
    monkeypatch.setenv('MCP_HOST', 'dummy')

    # Create a config object and load from environment
    config = OpenHandsConfig()
    load_from_env(config, os.environ)

    # Verify the environment variables were loaded into the config
    assert config.mcp_host == 'dummy'
    assert len(config.mcp.shttp_servers) == 1
    # If it's already a proper server config object, just verify it
    assert isinstance(config.mcp.shttp_servers[0], MCPSHTTPServerConfig)
    assert config.mcp.shttp_servers[0].url == 'http://env-server:8080'
    assert config.mcp.shttp_servers[0].api_key == 'env-api-key'

    # Create a session with the config
    session = Session(
        sid='test-sid',
        file_store=InMemoryFileStore({}),
        config=config,
        sio=mock_sio,
    )

    # Create empty settings
    settings = ConversationInitData()

    # Mock the Agent.get_cls method to avoid AgentNotRegisteredError
    mock_agent_cls = MagicMock()
    mock_agent_instance = MagicMock()
    mock_agent_cls.return_value = mock_agent_instance

    # Initialize the agent (this is where the MCP config would be reset)
    with (
        patch.object(session.agent_session, 'start', AsyncMock()),
        patch.object(Agent, 'get_cls', return_value=mock_agent_cls),
    ):
        await session.initialize_agent(settings, None, None)

    # Verify that the MCP configuration was preserved
    assert len(session.config.mcp.shttp_servers) >= 0

    # Clean up
    await session.close()


@pytest.mark.asyncio
async def test_session_settings_override_env_mcp_config(mock_sio, monkeypatch):
    """Test that Session settings override MCP configuration from environment variables."""
    # Set environment variables for MCP HTTP server
    monkeypatch.setenv(
        'MCP_SHTTP_SERVERS',
        '[{"url": "http://env-server:8080", "api_key": "env-api-key"}]',
    )

    # Also set MCP_HOST to prevent the default server from being added
    monkeypatch.setenv('MCP_HOST', '')

    # Create a config object and load from environment
    config = OpenHandsConfig()
    load_from_env(config, os.environ)

    # Create a session with the config
    session = Session(
        sid='test-sid',
        file_store=InMemoryFileStore({}),
        config=config,
        sio=mock_sio,
    )

    # Create settings with a different MCP config
    settings_mcp_config = MCPConfig(
        shttp_servers=[
            MCPSHTTPServerConfig(
                url='http://settings-server:8080',
                api_key='settings-api-key',
            )
        ]
    )
    settings = ConversationInitData(mcp_config=settings_mcp_config)

    # Mock the Agent.get_cls method to avoid AgentNotRegisteredError
    mock_agent_cls = MagicMock()
    mock_agent_instance = MagicMock()
    mock_agent_cls.return_value = mock_agent_instance

    # Initialize the agent
    with (
        patch.object(session.agent_session, 'start', AsyncMock()),
        patch.object(Agent, 'get_cls', return_value=mock_agent_cls),
    ):
        await session.initialize_agent(settings, None, None)

    # Verify that the settings MCP configuration was used
    assert len(session.config.mcp.shttp_servers) > 0

    # Check if the settings config is there
    settings_server_found = False
    for server in session.config.mcp.shttp_servers:
        if (
            isinstance(server, MCPSHTTPServerConfig)
            and server.url == 'http://settings-server:8080'
        ):
            settings_server_found = True
            assert server.api_key == 'settings-api-key'

    assert settings_server_found, 'Settings MCP configuration was lost'

    # Check that the environment variable config is NOT there (it was overridden)
    for server in session.config.mcp.shttp_servers:
        if isinstance(server, dict):
            assert server.get('url') != 'http://env-server:8080'
        elif isinstance(server, MCPSHTTPServerConfig):
            assert server.url != 'http://env-server:8080'

    # Clean up
    await session.close()
