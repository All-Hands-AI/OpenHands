"""Tests for CLI TUI MCP functionality."""

from unittest.mock import patch

from openhands.cli.tui import (
    display_mcp_action,
    display_mcp_errors,
    display_mcp_observation,
)
from openhands.events.action.mcp import MCPAction
from openhands.events.observation.mcp import MCPObservation
from openhands.mcp.error_collector import MCPError


class TestMCPTUIDisplay:
    """Test MCP TUI display functions."""

    @patch('openhands.cli.tui.print_container')
    def test_display_mcp_action_with_arguments(self, mock_print_container):
        """Test displaying MCP action with arguments."""
        mcp_action = MCPAction(
            name='test_tool', arguments={'param1': 'value1', 'param2': 42}
        )

        display_mcp_action(mcp_action)

        mock_print_container.assert_called_once()
        container = mock_print_container.call_args[0][0]
        assert 'test_tool' in container.body.text
        assert 'param1' in container.body.text
        assert 'value1' in container.body.text

    @patch('openhands.cli.tui.print_container')
    def test_display_mcp_action_no_arguments(self, mock_print_container):
        """Test displaying MCP action without arguments."""
        mcp_action = MCPAction(name='test_tool')

        display_mcp_action(mcp_action)

        mock_print_container.assert_called_once()
        container = mock_print_container.call_args[0][0]
        assert 'test_tool' in container.body.text
        # Should not contain arguments section when no arguments
        assert 'Arguments:' not in container.body.text

    @patch('openhands.cli.tui.print_container')
    def test_display_mcp_observation_with_content(self, mock_print_container):
        """Test displaying MCP observation with content."""
        mcp_observation = MCPObservation(
            content='Tool execution successful',
            name='test_tool',
            arguments={'param': 'value'},
        )

        display_mcp_observation(mcp_observation)

        mock_print_container.assert_called_once()
        container = mock_print_container.call_args[0][0]
        assert 'test_tool' in container.body.text
        assert 'Tool execution successful' in container.body.text

    @patch('openhands.cli.tui.print_container')
    def test_display_mcp_observation_no_content(self, mock_print_container):
        """Test displaying MCP observation without content."""
        mcp_observation = MCPObservation(content='', name='test_tool')

        display_mcp_observation(mcp_observation)

        mock_print_container.assert_called_once()
        container = mock_print_container.call_args[0][0]
        assert 'No output' in container.body.text

    @patch('openhands.cli.tui.print_formatted_text')
    @patch('openhands.mcp.error_collector.mcp_error_collector')
    def test_display_mcp_errors_no_errors(self, mock_collector, mock_print):
        """Test displaying MCP errors when none exist."""
        mock_collector.get_errors.return_value = []

        display_mcp_errors()

        mock_print.assert_called_once()
        call_args = mock_print.call_args[0][0]
        assert 'No MCP errors detected' in str(call_args)

    @patch('openhands.cli.tui.print_container')
    @patch('openhands.cli.tui.print_formatted_text')
    @patch('openhands.mcp.error_collector.mcp_error_collector')
    def test_display_mcp_errors_with_errors(
        self, mock_collector, mock_print, mock_print_container
    ):
        """Test displaying MCP errors when some exist."""
        # Create mock errors
        error1 = MCPError(
            timestamp=1234567890.0,
            server_name='test-server-1',
            server_type='stdio',
            error_message='Connection failed',
            exception_details='Socket timeout',
        )
        error2 = MCPError(
            timestamp=1234567891.0,
            server_name='test-server-2',
            server_type='sse',
            error_message='Server unreachable',
        )

        mock_collector.get_errors.return_value = [error1, error2]

        display_mcp_errors()

        # Should print error count header
        assert mock_print.call_count >= 1
        header_call = mock_print.call_args_list[0][0][0]
        assert '2 MCP error(s) detected' in str(header_call)

        # Should print containers for each error
        assert mock_print_container.call_count == 2

    @patch('openhands.cli.tui.print_container')
    def test_display_mcp_action_json_serialization_error(self, mock_print_container):
        """Test displaying MCP action when JSON serialization fails."""

        # Create an action with non-serializable arguments
        class NonSerializable:
            pass

        mcp_action = MCPAction(name='test_tool', arguments={'param': NonSerializable()})

        display_mcp_action(mcp_action)

        mock_print_container.assert_called_once()
        container = mock_print_container.call_args[0][0]
        assert 'test_tool' in container.body.text
        # Should fall back to str() representation
        assert 'NonSerializable' in container.body.text

    @patch('openhands.cli.tui.print_container')
    def test_display_mcp_observation_json_serialization_error(
        self, mock_print_container
    ):
        """Test displaying MCP observation when JSON serialization fails."""

        # Create an observation with non-serializable arguments
        class NonSerializable:
            pass

        mcp_observation = MCPObservation(
            content='Tool result',
            name='test_tool',
            arguments={'param': NonSerializable()},
        )

        display_mcp_observation(mcp_observation)

        mock_print_container.assert_called_once()
        container = mock_print_container.call_args[0][0]
        assert 'test_tool' in container.body.text
        assert 'Tool result' in container.body.text
        # Should fall back to str() representation for arguments
        assert 'NonSerializable' in container.body.text

    @patch('openhands.cli.tui.print_container')
    @patch('openhands.cli.tui.print_formatted_text')
    @patch('openhands.mcp.error_collector.mcp_error_collector')
    def test_display_mcp_errors_with_exception_details(
        self, mock_collector, mock_print, mock_print_container
    ):
        """Test displaying MCP errors with exception details."""
        error = MCPError(
            timestamp=1234567890.0,
            server_name='test-server',
            server_type='stdio',
            error_message='Connection failed',
            exception_details='Traceback: socket.timeout',
        )

        mock_collector.get_errors.return_value = [error]

        display_mcp_errors()

        # Should print error container
        mock_print_container.assert_called_once()
        container = mock_print_container.call_args[0][0]

        # Check that error details are included
        assert 'test-server' in container.body.text
        assert 'Connection failed' in container.body.text
        assert 'Traceback: socket.timeout' in container.body.text

    @patch('openhands.cli.tui.print_container')
    @patch('openhands.cli.tui.print_formatted_text')
    @patch('openhands.mcp.error_collector.mcp_error_collector')
    def test_display_mcp_errors_without_exception_details(
        self, mock_collector, mock_print, mock_print_container
    ):
        """Test displaying MCP errors without exception details."""
        error = MCPError(
            timestamp=1234567890.0,
            server_name='test-server',
            server_type='sse',
            error_message='Server unreachable',
        )

        mock_collector.get_errors.return_value = [error]

        display_mcp_errors()

        # Should print error container
        mock_print_container.assert_called_once()
        container = mock_print_container.call_args[0][0]

        # Check that basic error info is included
        assert 'test-server' in container.body.text
        assert 'Server unreachable' in container.body.text
        # Should not contain details section when no exception details
        assert 'Details:' not in container.body.text
