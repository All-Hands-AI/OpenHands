from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest

from openhands.core.config.mcp_config import MCPStdioServerConfig
from openhands.core.exceptions import (
    AgentRuntimeDisconnectedError,
    AgentRuntimeTimeoutError,
)
from openhands.events.action import CmdRunAction, MCPAction
from openhands.events.event import EventSource
from openhands.events.observation import ErrorObservation, Observation
from openhands.runtime.base import Runtime


class TestRuntimeErrorHandling:
    """Tests for runtime error handling functionality."""

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
        runtime.send_error_message = Mock()
        runtime.config = Mock()
        runtime.config.sandbox = Mock()
        return runtime

    @pytest.mark.asyncio
    async def test_handle_runtime_error_resets_mcp_servers(self, mock_runtime):
        """Test that _handle_runtime_error resets _last_updated_mcp_stdio_servers."""
        # Create a command action
        action = CmdRunAction(command='test command')
        action.set_hard_timeout(120)

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
    async def test_handle_runtime_error_on_disconnected(self, mock_runtime):
        """Test that _handle_runtime_error handles disconnected errors correctly."""
        # Create a command action
        action = CmdRunAction(command='test command')
        action.set_hard_timeout(120)

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
    async def test_handle_runtime_error_on_http_error(self, mock_runtime):
        """Test that _handle_runtime_error handles HTTP errors correctly."""
        # Create a command action
        action = CmdRunAction(command='test command')
        action.set_hard_timeout(120)

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
    async def test_handle_runtime_error_on_max_retries(self, mock_runtime):
        """Test that _handle_runtime_error handles max retries correctly."""
        # Create a command action
        action = CmdRunAction(command='test command')
        action.set_hard_timeout(120)

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

    @pytest.mark.asyncio
    async def test_execute_action_core(self, mock_runtime):
        """Test the _execute_action_core method."""
        # Create a command action
        action = CmdRunAction(command='test command')

        # Mock the run_action method
        mock_observation = Mock(spec=Observation)
        mock_runtime.run_action = Mock(return_value=mock_observation)

        # Patch the call_sync_from_async function
        with patch(
            'openhands.runtime.base.call_sync_from_async',
            return_value=mock_observation,
        ):
            # Call the method
            result = await Runtime._execute_action_core(mock_runtime, action)

            # Verify the result
            assert result == mock_observation

            # Verify _export_latest_git_provider_tokens was called
            mock_runtime._export_latest_git_provider_tokens.assert_called_once_with(
                action
            )

    @pytest.mark.asyncio
    async def test_execute_action_core_with_mcp_action(self, mock_runtime):
        """Test the _execute_action_core method with an MCP action."""
        # Create an MCP action
        action = Mock(spec=MCPAction)

        # Mock the call_tool_mcp method
        mock_observation = Mock(spec=Observation)
        mock_runtime.call_tool_mcp = AsyncMock(return_value=mock_observation)

        # Call the method
        result = await Runtime._execute_action_core(mock_runtime, action)

        # Verify the result
        assert result == mock_observation

        # Verify _export_latest_git_provider_tokens was called
        mock_runtime._export_latest_git_provider_tokens.assert_called_once_with(action)

        # Verify call_tool_mcp was called
        mock_runtime.call_tool_mcp.assert_called_once_with(action)

    @pytest.mark.asyncio
    async def test_handle_action_with_retry_enabled(self, mock_runtime):
        """Test _handle_action with retry enabled."""
        # Configure the mock runtime
        mock_runtime.config.sandbox.retry_on_unrecoverable_runtime_error = True

        # Create a command action
        action = CmdRunAction(command='test command')
        action.set_hard_timeout(120)

        # Mock the _execute_action_core method
        mock_observation = Mock(spec=Observation)
        mock_runtime._execute_action_core = AsyncMock(return_value=mock_observation)

        # Since we can't easily mock the tenacity.retry decorator directly,
        # we'll test the behavior by checking that the right configuration is used
        # when retry_on_unrecoverable_runtime_error is True

        # Call the method with a patched _execute_action_core
        await Runtime._handle_action(mock_runtime, action)

        # Verify _execute_action_core was called
        mock_runtime._execute_action_core.assert_called_once_with(action)

        # Verify the observation was processed correctly
        assert hasattr(mock_observation, '_cause')
        assert hasattr(mock_observation, 'tool_call_metadata')

    @pytest.mark.asyncio
    async def test_handle_action_with_retry_disabled(self, mock_runtime):
        """Test _handle_action with retry disabled."""
        # Configure the mock runtime
        mock_runtime.config.sandbox.retry_on_unrecoverable_runtime_error = False

        # Create a command action
        action = CmdRunAction(command='test command')
        action.set_hard_timeout(120)

        # Mock the _execute_action_core method
        mock_observation = Mock(spec=Observation)
        mock_runtime._execute_action_core = AsyncMock(return_value=mock_observation)

        # Call the method
        await Runtime._handle_action(mock_runtime, action)

        # Verify _execute_action_core was called
        mock_runtime._execute_action_core.assert_called_once_with(action)

        # Verify the observation was added to the event stream
        assert mock_observation._cause == action.id
        assert mock_observation.tool_call_metadata == action.tool_call_metadata

    @pytest.mark.asyncio
    async def test_handle_action_with_runtime_error(self, mock_runtime):
        """Test _handle_action when a runtime error occurs."""
        # Configure the mock runtime
        mock_runtime.config.sandbox.retry_on_unrecoverable_runtime_error = False

        # Create a command action
        action = CmdRunAction(command='test command')
        action.set_hard_timeout(120)

        # Mock the _execute_action_core method to raise an error
        error = AgentRuntimeDisconnectedError('Runtime disconnected')
        mock_runtime._execute_action_core = AsyncMock(side_effect=error)

        # Call the method
        await Runtime._handle_action(mock_runtime, action)

        # Verify _execute_action_core was called
        mock_runtime._execute_action_core.assert_called_once_with(action)

        # Verify send_error_message was called
        mock_runtime.send_error_message.assert_called_once_with(
            'STATUS$ERROR_RUNTIME_DISCONNECTED',
            'AgentRuntimeDisconnectedError: Runtime disconnected',
        )

    @pytest.mark.asyncio
    async def test_handle_action_with_other_exception(self, mock_runtime):
        """Test _handle_action when a non-runtime error occurs."""
        # Configure the mock runtime
        mock_runtime.config.sandbox.retry_on_unrecoverable_runtime_error = False

        # Create a command action
        action = CmdRunAction(command='test command')
        action.set_hard_timeout(120)

        # Mock the _execute_action_core method to raise an error
        error = ValueError('Invalid value')
        mock_runtime._execute_action_core = AsyncMock(side_effect=error)

        # Call the method
        await Runtime._handle_action(mock_runtime, action)

        # Verify _execute_action_core was called
        mock_runtime._execute_action_core.assert_called_once_with(action)

        # Verify send_error_message was called
        mock_runtime.send_error_message.assert_called_once_with(
            '', 'ValueError: Invalid value'
        )

    @pytest.mark.asyncio
    async def test_handle_action_with_network_error(self, mock_runtime):
        """Test _handle_action when a network error occurs."""
        # Configure the mock runtime
        mock_runtime.config.sandbox.retry_on_unrecoverable_runtime_error = False

        # Create a command action
        action = CmdRunAction(command='test command')
        action.set_hard_timeout(120)

        # Mock the _execute_action_core method to raise an error
        error = httpx.NetworkError('Connection error')
        mock_runtime._execute_action_core = AsyncMock(side_effect=error)

        # Call the method
        await Runtime._handle_action(mock_runtime, action)

        # Verify _execute_action_core was called
        mock_runtime._execute_action_core.assert_called_once_with(action)

        # Verify send_error_message was called
        mock_runtime.send_error_message.assert_called_once_with(
            'STATUS$ERROR_RUNTIME_DISCONNECTED', 'NetworkError: Connection error'
        )
