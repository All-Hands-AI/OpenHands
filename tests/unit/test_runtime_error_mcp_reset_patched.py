from unittest.mock import Mock, patch

import httpx
import pytest

from openhands.core.config.mcp_config import MCPStdioServerConfig
from openhands.core.exceptions import (
    AgentRuntimeDisconnectedError,
    AgentRuntimeTimeoutError,
)
from openhands.events.action import CmdRunAction
from openhands.runtime.base import Runtime


@pytest.fixture
def mock_runtime():
    """Create a mock Runtime with necessary attributes."""
    runtime = Mock(spec=Runtime)
    runtime._last_updated_mcp_stdio_servers = [
        MCPStdioServerConfig(name='test-server-1', command='test-command-1'),
        MCPStdioServerConfig(name='test-server-2', command='test-command-2'),
    ]
    runtime.log = Mock()
    runtime.event_stream = Mock()
    return runtime


@pytest.mark.asyncio
async def test_reset_mcp_servers_on_timeout_error(mock_runtime):
    """Test that _last_updated_mcp_stdio_servers is reset when a timeout error occurs."""
    # Create a command action
    action = CmdRunAction(command='test command')
    action.set_hard_timeout(120)

    # Verify initial state
    assert len(mock_runtime._last_updated_mcp_stdio_servers) == 2

    # Patch the id property to return a valid integer
    with patch(
        'openhands.events.action.commands.CmdRunAction.id',
        new_callable=Mock,
        return_value=12345,
    ):
        # Call the actual implementation to test the reset functionality
        await Runtime._handle_runtime_error(
            mock_runtime,
            action,
            AgentRuntimeTimeoutError('Runtime timeout'),
            retry_count=1,
            max_retries=3,
        )

    # Verify _last_updated_mcp_stdio_servers was reset
    assert mock_runtime._last_updated_mcp_stdio_servers == []

    # Verify log message was called
    mock_runtime.log.assert_any_call(
        'debug',
        'Reset _last_updated_mcp_stdio_servers to empty list due to runtime error',
    )


@pytest.mark.asyncio
async def test_reset_mcp_servers_on_disconnected_error(mock_runtime):
    """Test that _last_updated_mcp_stdio_servers is reset when a disconnected error occurs."""
    # Create a command action
    action = CmdRunAction(command='test command')
    action.set_hard_timeout(120)

    # Verify initial state
    assert len(mock_runtime._last_updated_mcp_stdio_servers) == 2

    # Patch the id property to return a valid integer
    with patch(
        'openhands.events.action.commands.CmdRunAction.id',
        new_callable=Mock,
        return_value=12345,
    ):
        # Call the actual implementation to test the reset functionality
        await Runtime._handle_runtime_error(
            mock_runtime,
            action,
            AgentRuntimeDisconnectedError('Runtime disconnected'),
            retry_count=1,
            max_retries=3,
        )

    # Verify _last_updated_mcp_stdio_servers was reset
    assert mock_runtime._last_updated_mcp_stdio_servers == []

    # Verify log message was called
    mock_runtime.log.assert_any_call(
        'debug',
        'Reset _last_updated_mcp_stdio_servers to empty list due to runtime error',
    )


@pytest.mark.asyncio
async def test_reset_mcp_servers_on_http_error(mock_runtime):
    """Test that _last_updated_mcp_stdio_servers is reset when an HTTP error occurs."""
    # Create a command action
    action = CmdRunAction(command='test command')
    action.set_hard_timeout(120)

    # Create a mock response with a 502 status code
    mock_response = Mock()
    mock_response.status_code = 502

    # Verify initial state
    assert len(mock_runtime._last_updated_mcp_stdio_servers) == 2

    # Patch the id property to return a valid integer
    with patch(
        'openhands.events.action.commands.CmdRunAction.id',
        new_callable=Mock,
        return_value=12345,
    ):
        # Call the actual implementation to test the reset functionality
        await Runtime._handle_runtime_error(
            mock_runtime,
            action,
            httpx.HTTPStatusError(
                'Bad Gateway', request=Mock(), response=mock_response
            ),
            retry_count=1,
            max_retries=3,
        )

    # Verify _last_updated_mcp_stdio_servers was reset
    assert mock_runtime._last_updated_mcp_stdio_servers == []

    # Verify log message was called
    mock_runtime.log.assert_any_call(
        'debug',
        'Reset _last_updated_mcp_stdio_servers to empty list due to runtime error',
    )


@pytest.mark.asyncio
async def test_reset_mcp_servers_on_generic_exception(mock_runtime):
    """Test that _last_updated_mcp_stdio_servers is reset when a generic exception occurs."""
    # Create a command action
    action = CmdRunAction(command='test command')
    action.set_hard_timeout(120)

    # Verify initial state
    assert len(mock_runtime._last_updated_mcp_stdio_servers) == 2

    # Patch the id property to return a valid integer
    with patch(
        'openhands.events.action.commands.CmdRunAction.id',
        new_callable=Mock,
        return_value=12345,
    ):
        # Call the actual implementation to test the reset functionality
        await Runtime._handle_runtime_error(
            mock_runtime,
            action,
            Exception('Generic error'),
            retry_count=1,
            max_retries=3,
        )

    # Verify _last_updated_mcp_stdio_servers was reset
    assert mock_runtime._last_updated_mcp_stdio_servers == []

    # Verify log message was called
    mock_runtime.log.assert_any_call(
        'debug',
        'Reset _last_updated_mcp_stdio_servers to empty list due to runtime error',
    )
