from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest

from openhands.core.config.mcp_config import MCPStdioServerConfig
from openhands.core.exceptions import (
    AgentRuntimeDisconnectedError,
    AgentRuntimeTimeoutError,
)
from openhands.events.action import CmdRunAction
from openhands.events.event import EventSource
from openhands.events.observation import ErrorObservation
from openhands.runtime.base import Runtime


class TestRuntimeErrorHandlingSimplified:
    """Simplified tests for runtime error handling."""

    @pytest.fixture
    def mock_runtime(self):
        """Create a mock Runtime with necessary attributes."""
        runtime = Mock(spec=Runtime)
        runtime._last_updated_mcp_stdio_servers = [
            MCPStdioServerConfig(name='test-server-1', command='test-command-1'),
            MCPStdioServerConfig(name='test-server-2', command='test-command-2'),
        ]
        runtime.log = Mock()
        runtime.event_stream = Mock()
        runtime.event_stream.add_event = AsyncMock()
        return runtime

    @pytest.mark.asyncio
    async def test_handle_runtime_error_resets_mcp_servers_on_timeout(
        self, mock_runtime
    ):
        """Test that _handle_runtime_error resets _last_updated_mcp_stdio_servers on timeout."""
        # Create a command action
        action = CmdRunAction(command='test command')

        # Patch the id property to return a valid integer
        with patch(
            'openhands.events.action.commands.CmdRunAction.id',
            new_callable=Mock,
            return_value=12345,
        ):
            # Call the error handling method directly
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

            # Verify an error observation was added to the event stream
            mock_runtime.event_stream.add_event.assert_called_once()

            # Get the observation that was added
            call_args = mock_runtime.event_stream.add_event.call_args[0]
            observation = call_args[0]
            source = call_args[1]

            # Verify it's an ErrorObservation with the right source
            assert isinstance(observation, ErrorObservation)
            assert source == EventSource.ENVIRONMENT

            # Verify the error message contains the standard runtime error text
            assert (
                'Your command may have consumed too much resources'
                in observation.content
            )
            assert 'Retry 1 of 3' in observation.content

    @pytest.mark.asyncio
    async def test_handle_runtime_error_resets_mcp_servers_on_disconnected(
        self, mock_runtime
    ):
        """Test that _handle_runtime_error resets _last_updated_mcp_stdio_servers on disconnected error."""
        # Create a command action
        action = CmdRunAction(command='test command')

        # Patch the id property to return a valid integer
        with patch(
            'openhands.events.action.commands.CmdRunAction.id',
            new_callable=Mock,
            return_value=12345,
        ):
            # Call the error handling method directly
            await Runtime._handle_runtime_error(
                mock_runtime,
                action,
                AgentRuntimeDisconnectedError('Runtime disconnected'),
                retry_count=2,
                max_retries=3,
            )

            # Verify _last_updated_mcp_stdio_servers was reset
            assert mock_runtime._last_updated_mcp_stdio_servers == []

            # Verify log message was called
            mock_runtime.log.assert_any_call(
                'debug',
                'Reset _last_updated_mcp_stdio_servers to empty list due to runtime error',
            )

            # Verify an error observation was added to the event stream
            mock_runtime.event_stream.add_event.assert_called_once()

            # Get the observation that was added
            call_args = mock_runtime.event_stream.add_event.call_args[0]
            observation = call_args[0]
            source = call_args[1]

            # Verify it's an ErrorObservation with the right source
            assert isinstance(observation, ErrorObservation)
            assert source == EventSource.ENVIRONMENT

            # Verify the error message contains the standard runtime error text
            assert (
                'Your command may have consumed too much resources'
                in observation.content
            )
            assert 'Retry 2 of 3' in observation.content

    @pytest.mark.asyncio
    async def test_handle_runtime_error_resets_mcp_servers_on_http_error(
        self, mock_runtime
    ):
        """Test that _handle_runtime_error resets _last_updated_mcp_stdio_servers on HTTP error."""
        # Create a command action
        action = CmdRunAction(command='test command')

        # Create a mock response with a 502 status code
        mock_response = Mock()
        mock_response.status_code = 502

        # Patch the id property to return a valid integer
        with patch(
            'openhands.events.action.commands.CmdRunAction.id',
            new_callable=Mock,
            return_value=12345,
        ):
            # Call the error handling method directly
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

            # Verify an error observation was added to the event stream
            mock_runtime.event_stream.add_event.assert_called_once()

            # Get the observation that was added
            call_args = mock_runtime.event_stream.add_event.call_args[0]
            observation = call_args[0]
            source = call_args[1]

            # Verify it's an ErrorObservation with the right source
            assert isinstance(observation, ErrorObservation)
            assert source == EventSource.ENVIRONMENT

            # Verify the error message contains the standard runtime error text
            assert (
                'Your command may have consumed too much resources'
                in observation.content
            )
            assert 'Retry 1 of 3' in observation.content

    @pytest.mark.asyncio
    async def test_handle_runtime_error_resets_mcp_servers_on_max_retries(
        self, mock_runtime
    ):
        """Test that _handle_runtime_error resets _last_updated_mcp_stdio_servers when max retries are reached."""
        # Create a command action
        action = CmdRunAction(command='test command')

        # Patch the id property to return a valid integer
        with patch(
            'openhands.events.action.commands.CmdRunAction.id',
            new_callable=Mock,
            return_value=12345,
        ):
            # Call the error handling method directly
            await Runtime._handle_runtime_error(
                mock_runtime,
                action,
                Exception('Generic error'),
                retry_count=3,  # Same as max_retries
                max_retries=3,
            )

            # Verify _last_updated_mcp_stdio_servers was reset
            assert mock_runtime._last_updated_mcp_stdio_servers == []

            # Verify log message was called
            mock_runtime.log.assert_any_call(
                'debug',
                'Reset _last_updated_mcp_stdio_servers to empty list due to runtime error',
            )

            # Verify an error observation was added to the event stream
            mock_runtime.event_stream.add_event.assert_called_once()

            # Get the observation that was added
            call_args = mock_runtime.event_stream.add_event.call_args[0]
            observation = call_args[0]
            source = call_args[1]

            # Verify it's an ErrorObservation with the right source
            assert isinstance(observation, ErrorObservation)
            assert source == EventSource.ENVIRONMENT

            # Verify the error message contains the standard runtime error text
            assert (
                'Your command may have consumed too much resources'
                in observation.content
            )
            assert 'Retry 3 of 3' in observation.content
