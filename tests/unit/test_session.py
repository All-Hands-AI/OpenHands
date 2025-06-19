from unittest.mock import ANY, AsyncMock, patch

import pytest
from litellm.exceptions import (
    RateLimitError,
)

from openhands.core.config.llm_config import LLMConfig
from openhands.core.config.mcp_config import MCPConfig, MCPSSEServerConfig
from openhands.core.config.openhands_config import OpenHandsConfig
from openhands.server.session.session import Session
from openhands.storage.data_models.settings import Settings
from openhands.storage.memory import InMemoryFileStore


@pytest.fixture
def mock_status_callback():
    return AsyncMock()


@pytest.fixture
def mock_sio():
    return AsyncMock()


@pytest.fixture
def default_llm_config():
    return LLMConfig(
        model='gpt-4o',
        api_key='test_key',
        num_retries=2,
        retry_min_wait=1,
        retry_max_wait=2,
    )


@pytest.mark.asyncio
@patch('openhands.llm.llm.litellm_completion')
async def test_notify_on_llm_retry(
    mock_litellm_completion, mock_sio, default_llm_config
):
    config = OpenHandsConfig()
    config.set_llm_config(default_llm_config)
    session = Session(
        sid='..sid..',
        file_store=InMemoryFileStore({}),
        config=config,
        sio=mock_sio,
        user_id='..uid..',
    )
    session.queue_status_message = AsyncMock()

    with patch('time.sleep') as _mock_sleep:
        mock_litellm_completion.side_effect = [
            RateLimitError(
                'Rate limit exceeded', llm_provider='test_provider', model='test_model'
            ),
            {'choices': [{'message': {'content': 'Retry successful'}}]},
        ]
    llm = session._create_llm('..cls..')

    llm.completion(
        messages=[{'role': 'user', 'content': 'Hello!'}],
        stream=False,
    )

    assert mock_litellm_completion.call_count == 2
    session.queue_status_message.assert_called_once_with(
        'info', 'STATUS$LLM_RETRY', ANY
    )
    await session.close()


@pytest.mark.asyncio
async def test_mcp_config_priority():
    """Test MCP configuration priority logic in Session.initialize_agent."""

    # Test case 1: Both config.mcp and settings.mcp_config exist - config.mcp should win
    config = OpenHandsConfig()
    config.mcp = MCPConfig(
        sse_servers=[MCPSSEServerConfig(url='http://config-server.com')]
    )

    settings = Settings(
        mcp_config=MCPConfig(
            sse_servers=[MCPSSEServerConfig(url='http://settings-server.com')]
        )
    )

    session = Session(
        sid='test-sid',
        file_store=InMemoryFileStore({}),
        config=config,
        sio=None,
        user_id='test-user',
    )

    # Mock the agent session initialization to avoid complex dependencies
    with patch.object(session.agent_session, 'start', new_callable=AsyncMock):
        with patch('openhands.controller.agent.Agent.get_cls') as mock_get_cls:
            mock_agent_cls = AsyncMock()
            mock_get_cls.return_value = mock_agent_cls

            await session.initialize_agent(settings, None, None)

            # Verify that config.mcp was used (config-first priority)
            assert len(session.config.mcp.sse_servers) >= 1
            # Should contain the config server
            config_server_found = any(
                server.url == 'http://config-server.com'
                for server in session.config.mcp.sse_servers
            )
            assert config_server_found, 'config.mcp should be used as source of truth'

            # Should not contain the settings server (before OpenHands default servers are added)
            settings_server_found = any(
                server.url == 'http://settings-server.com'
                for server in session.config.mcp.sse_servers
            )
            assert not settings_server_found, (
                'settings.mcp_config should be overridden by config.mcp'
            )

    await session.close()

    # Test case 2: Only settings.mcp_config exists - should use settings
    config = OpenHandsConfig()  # Empty MCP config
    settings = Settings(
        mcp_config=MCPConfig(
            sse_servers=[MCPSSEServerConfig(url='http://settings-server.com')]
        )
    )

    session = Session(
        sid='test-sid-2',
        file_store=InMemoryFileStore({}),
        config=config,
        sio=None,
        user_id='test-user',
    )

    with patch.object(session.agent_session, 'start', new_callable=AsyncMock):
        with patch('openhands.controller.agent.Agent.get_cls') as mock_get_cls:
            mock_agent_cls = AsyncMock()
            mock_get_cls.return_value = mock_agent_cls

            await session.initialize_agent(settings, None, None)

            # Should contain the settings server
            settings_server_found = any(
                server.url == 'http://settings-server.com'
                for server in session.config.mcp.sse_servers
            )
            assert settings_server_found, (
                'settings.mcp_config should be used as fallback'
            )

    await session.close()

    # Test case 3: Only config.mcp exists (no settings) - should use config
    config = OpenHandsConfig()
    config.mcp = MCPConfig(
        sse_servers=[MCPSSEServerConfig(url='http://config-server.com')]
    )
    settings = Settings()  # No mcp_config

    session = Session(
        sid='test-sid-3',
        file_store=InMemoryFileStore({}),
        config=config,
        sio=None,
        user_id='test-user',
    )

    with patch.object(session.agent_session, 'start', new_callable=AsyncMock):
        with patch('openhands.controller.agent.Agent.get_cls') as mock_get_cls:
            mock_agent_cls = AsyncMock()
            mock_get_cls.return_value = mock_agent_cls

            await session.initialize_agent(settings, None, None)

            # Should contain the config server
            config_server_found = any(
                server.url == 'http://config-server.com'
                for server in session.config.mcp.sse_servers
            )
            assert config_server_found, (
                'config.mcp should be used when no settings available'
            )

    await session.close()

    # Test case 4: Neither config nor settings have MCP - should use empty config
    config = OpenHandsConfig()  # Empty MCP config
    settings = Settings()  # No mcp_config

    session = Session(
        sid='test-sid-4',
        file_store=InMemoryFileStore({}),
        config=config,
        sio=None,
        user_id='test-user',
    )

    with patch.object(session.agent_session, 'start', new_callable=AsyncMock):
        with patch('openhands.controller.agent.Agent.get_cls') as mock_get_cls:
            mock_agent_cls = AsyncMock()
            mock_get_cls.return_value = mock_agent_cls

            await session.initialize_agent(settings, None, None)

            # Should have empty MCP config (except for OpenHands default servers)
            # The default OpenHands MCP server should still be added
            assert session.config.mcp is not None
            # Check that it's a valid MCPConfig instance
            assert isinstance(session.config.mcp, MCPConfig)

    await session.close()
