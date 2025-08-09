"""Tests for the bash reset terminal functionality."""

import pytest
from unittest.mock import Mock, patch

from openhands.events.action import CmdRunAction
from openhands.events.observation import CmdOutputObservation
from openhands.runtime.utils.bash import BashSession


class TestBashResetTerminal:
    """Test cases for the reset_terminal functionality."""

    def test_cmd_run_action_with_reset_terminal(self):
        """Test that CmdRunAction can be created with reset_terminal parameter."""
        action = CmdRunAction(command="", reset_terminal=True)
        assert action.reset_terminal is True

    def test_cmd_run_action_reset_terminal_default(self):
        """Test that reset_terminal defaults to False."""
        action = CmdRunAction(command="echo hello")
        assert action.reset_terminal is False

    @patch('openhands.runtime.utils.bash.libtmux')
    def test_bash_session_reset(self, mock_libtmux):
        """Test that BashSession.reset() properly resets the session."""
        # Mock the tmux server and session
        mock_server = Mock()
        mock_session = Mock()
        mock_window = Mock()
        mock_pane = Mock()

        mock_libtmux.Server.return_value = mock_server
        mock_server.new_session.return_value = mock_session
        mock_session.new_window.return_value = mock_window
        mock_window.active_pane = mock_pane
        mock_session.active_window = Mock()

        # Create bash session
        bash_session = BashSession(work_dir="/tmp", username="test")
        bash_session.initialize()

        # Store initial state
        initial_cwd = bash_session.cwd

        # Mock the close method to avoid actual tmux operations
        with patch.object(bash_session, 'close'):
            with patch.object(bash_session, 'initialize'):
                bash_session.reset()

                # Verify that close and initialize were called
                bash_session.close.assert_called_once()
                bash_session.initialize.assert_called_once()

    @patch('openhands.runtime.utils.bash.libtmux')
    def test_execute_with_reset_terminal(self, mock_libtmux):
        """Test that execute() handles reset_terminal parameter correctly."""
        # Mock the tmux server and session
        mock_server = Mock()
        mock_session = Mock()
        mock_window = Mock()
        mock_pane = Mock()

        mock_libtmux.Server.return_value = mock_server
        mock_server.new_session.return_value = mock_session
        mock_session.new_window.return_value = mock_window
        mock_window.active_pane = mock_pane
        mock_session.active_window = Mock()

        # Create bash session
        bash_session = BashSession(work_dir="/tmp", username="test")
        bash_session.initialize()

        # Create action with reset_terminal=True
        action = CmdRunAction(command="", reset_terminal=True)

        # Mock the reset method
        with patch.object(bash_session, 'reset') as mock_reset:
            result = bash_session.execute(action)

            # Verify reset was called
            mock_reset.assert_called_once()

            # Verify the result is a success message
            assert isinstance(result, CmdOutputObservation)
            assert "Terminal session has been reset successfully" in result.content

    def test_function_calling_reset_terminal_parameter(self):
        """Test that function calling properly handles reset_terminal parameter."""
        from openhands.agenthub.codeact_agent.function_calling import response_to_actions
        from openhands.agenthub.codeact_agent.tools.bash import create_cmd_run_tool
        from litellm import ModelResponse

        # Create a mock response with reset_terminal parameter
        mock_response = Mock(spec=ModelResponse)
        mock_response.id = "test_response_id"
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.tool_calls = [Mock()]
        mock_response.choices[0].message.tool_calls[0].function = Mock()
        mock_response.choices[0].message.tool_calls[0].function.name = create_cmd_run_tool()['function']['name']
        mock_response.choices[0].message.tool_calls[0].function.arguments = '{"command": "", "reset_terminal": true}'

        # Set the tool_call_id to a string
        mock_response.choices[0].message.tool_calls[0].id = "test_tool_call_id"

        # Test that the parameter is properly parsed
        actions = response_to_actions(mock_response)
        assert len(actions) == 1
        assert isinstance(actions[0], CmdRunAction)
        assert actions[0].reset_terminal is True
