"""Tests for CLI server management functionality."""

from unittest.mock import MagicMock, patch

import pytest

from openhands.cli.commands import (
    add_mcp_server,
    display_mcp_servers,
    remove_mcp_server,
)
from openhands.core.config import OpenHandsConfig
from openhands.core.config.mcp_config import (
    MCPConfig,
    MCPSSEServerConfig,
    MCPStdioServerConfig,
)


class TestMCPServerManagement:
    """Test MCP server management functions."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = MagicMock(spec=OpenHandsConfig)
        self.config.cli = MagicMock()
        self.config.cli.vi_mode = False

    @patch('openhands.cli.commands.print_formatted_text')
    def test_display_mcp_servers_no_servers(self, mock_print):
        """Test displaying MCP servers when none are configured."""
        self.config.mcp = MCPConfig()  # Empty config

        display_mcp_servers(self.config)

        mock_print.assert_called_once()
        call_args = mock_print.call_args[0][0]
        assert 'No custom MCP servers configured' in call_args

    @patch('openhands.cli.commands.print_formatted_text')
    def test_display_mcp_servers_with_servers(self, mock_print):
        """Test displaying MCP servers when some are configured."""
        self.config.mcp = MCPConfig(
            sse_servers=[MCPSSEServerConfig(url='http://test.com')],
            stdio_servers=[MCPStdioServerConfig(name='test-stdio', command='python')],
        )

        display_mcp_servers(self.config)

        # Should be called multiple times for different sections
        assert mock_print.call_count >= 2

        # Check that the summary is printed
        first_call = mock_print.call_args_list[0][0][0]
        assert 'Configured MCP servers:' in first_call
        assert 'SSE servers: 1' in first_call
        assert 'Stdio servers: 1' in first_call

    @pytest.mark.asyncio
    @patch('openhands.cli.commands.cli_confirm')
    @patch('openhands.cli.commands.add_sse_server')
    async def test_add_mcp_server_sse(self, mock_add_sse, mock_cli_confirm):
        """Test adding an SSE MCP server."""
        mock_cli_confirm.return_value = 0  # SSE option

        await add_mcp_server(self.config)

        mock_cli_confirm.assert_called_once()
        mock_add_sse.assert_called_once_with(self.config)

    @pytest.mark.asyncio
    @patch('openhands.cli.commands.cli_confirm')
    @patch('openhands.cli.commands.add_stdio_server')
    async def test_add_mcp_server_stdio(self, mock_add_stdio, mock_cli_confirm):
        """Test adding a Stdio MCP server."""
        mock_cli_confirm.return_value = 1  # Stdio option

        await add_mcp_server(self.config)

        mock_cli_confirm.assert_called_once()
        mock_add_stdio.assert_called_once_with(self.config)

    @pytest.mark.asyncio
    @patch('openhands.cli.commands.cli_confirm')
    async def test_add_mcp_server_cancel(self, mock_cli_confirm):
        """Test canceling MCP server addition."""
        mock_cli_confirm.return_value = 3  # Cancel option

        await add_mcp_server(self.config)

        mock_cli_confirm.assert_called_once()
        # No other functions should be called

    @pytest.mark.asyncio
    @patch('openhands.cli.commands.cli_confirm')
    @patch('openhands.cli.commands.print_formatted_text')
    async def test_remove_mcp_server_no_servers(self, mock_print, mock_cli_confirm):
        """Test removing MCP server when none are configured."""
        self.config.mcp = MCPConfig()  # Empty config

        await remove_mcp_server(self.config)

        mock_print.assert_called_once_with('No MCP servers configured to remove.')
        mock_cli_confirm.assert_not_called()

    @pytest.mark.asyncio
    @patch('openhands.cli.commands.cli_confirm')
    @patch('openhands.cli.commands.load_config_file')
    @patch('openhands.cli.commands.save_config_file')
    @patch('openhands.cli.commands.print_formatted_text')
    async def test_remove_mcp_server_success(
        self, mock_print, mock_save, mock_load, mock_cli_confirm
    ):
        """Test successfully removing an MCP server."""
        # Set up config with servers
        self.config.mcp = MCPConfig(
            sse_servers=[MCPSSEServerConfig(url='http://test.com')],
            stdio_servers=[MCPStdioServerConfig(name='test-stdio', command='python')],
        )

        # Mock user selections
        mock_cli_confirm.side_effect = [0, 0]  # Select first server, confirm removal

        # Mock config file operations
        mock_load.return_value = {
            'mcp': {
                'sse_servers': [{'url': 'http://test.com'}],
                'stdio_servers': [{'name': 'test-stdio', 'command': 'python'}],
            }
        }

        await remove_mcp_server(self.config)

        # Should have been called twice (select server, confirm removal)
        assert mock_cli_confirm.call_count == 2
        mock_save.assert_called_once()

        # Check that success message was printed
        success_calls = [
            call for call in mock_print.call_args_list if 'removed' in str(call[0][0])
        ]
        assert len(success_calls) >= 1
