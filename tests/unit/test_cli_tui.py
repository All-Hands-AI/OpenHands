from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from openhands.cli.tui import (
    CustomDiffLexer,
    UsageMetrics,
    UserCancelledError,
    display_banner,
    display_command,
    display_event,
    display_message,
    display_runtime_initialization_message,
    display_shutdown_message,
    display_status,
    display_usage_metrics,
    display_welcome_message,
    get_session_duration,
    read_confirmation_input,
)
from openhands.core.config import OpenHandsConfig
from openhands.events import EventSource
from openhands.events.action import (
    Action,
    ActionConfirmationStatus,
    CmdRunAction,
    MessageAction,
)
from openhands.events.observation import (
    CmdOutputObservation,
    FileEditObservation,
    FileReadObservation,
)
from openhands.llm.metrics import Metrics


class TestDisplayFunctions:
    @patch('openhands.cli.tui.print_formatted_text')
    def test_display_runtime_initialization_message_local(self, mock_print):
        display_runtime_initialization_message('local')
        assert mock_print.call_count == 3
        # Check the second call has the local runtime message
        args, kwargs = mock_print.call_args_list[1]
        assert 'Starting local runtime' in str(args[0])

    @patch('openhands.cli.tui.print_formatted_text')
    def test_display_runtime_initialization_message_docker(self, mock_print):
        display_runtime_initialization_message('docker')
        assert mock_print.call_count == 3
        # Check the second call has the docker runtime message
        args, kwargs = mock_print.call_args_list[1]
        assert 'Starting Docker runtime' in str(args[0])

    @patch('openhands.cli.tui.print_formatted_text')
    def test_display_banner(self, mock_print):
        session_id = 'test-session-id'

        display_banner(session_id)

        # Verify banner calls
        assert mock_print.call_count >= 3
        # Check the last call has the session ID
        args, kwargs = mock_print.call_args_list[-2]
        assert session_id in str(args[0])
        assert 'Initialized conversation' in str(args[0])

    @patch('openhands.cli.tui.print_formatted_text')
    def test_display_welcome_message(self, mock_print):
        display_welcome_message()
        assert mock_print.call_count == 2
        # Check the first call contains the welcome message
        args, kwargs = mock_print.call_args_list[0]
        assert "Let's start building" in str(args[0])

    @patch('openhands.cli.tui.display_message')
    def test_display_event_message_action(self, mock_display_message):
        config = MagicMock(spec=OpenHandsConfig)
        message = MessageAction(content='Test message')
        message._source = EventSource.AGENT

        display_event(message, config)

        mock_display_message.assert_called_once_with('Test message')

    @patch('openhands.cli.tui.display_command')
    def test_display_event_cmd_action(self, mock_display_command):
        config = MagicMock(spec=OpenHandsConfig)
        # Test that commands awaiting confirmation are displayed
        cmd_action = CmdRunAction(command='echo test')
        cmd_action.confirmation_state = ActionConfirmationStatus.AWAITING_CONFIRMATION

        display_event(cmd_action, config)

        mock_display_command.assert_called_once_with(cmd_action)

    @patch('openhands.cli.tui.display_command')
    @patch('openhands.cli.tui.initialize_streaming_output')
    def test_display_event_cmd_action_confirmed(
        self, mock_init_streaming, mock_display_command
    ):
        config = MagicMock(spec=OpenHandsConfig)
        # Test that confirmed commands don't display the command but do initialize streaming
        cmd_action = CmdRunAction(command='echo test')
        cmd_action.confirmation_state = ActionConfirmationStatus.CONFIRMED

        display_event(cmd_action, config)

        # Command should not be displayed (since it was already shown when awaiting confirmation)
        mock_display_command.assert_not_called()
        # But streaming should be initialized
        mock_init_streaming.assert_called_once()

    @patch('openhands.cli.tui.display_command_output')
    def test_display_event_cmd_output(self, mock_display_output):
        config = MagicMock(spec=OpenHandsConfig)
        cmd_output = CmdOutputObservation(content='Test output', command='echo test')

        display_event(cmd_output, config)

        mock_display_output.assert_called_once_with('Test output')

    @patch('openhands.cli.tui.display_file_edit')
    def test_display_event_file_edit_observation(self, mock_display_file_edit):
        config = MagicMock(spec=OpenHandsConfig)
        file_edit_obs = FileEditObservation(path='test.py', content="print('hello')")

        display_event(file_edit_obs, config)

        mock_display_file_edit.assert_called_once_with(file_edit_obs)

    @patch('openhands.cli.tui.display_file_read')
    def test_display_event_file_read(self, mock_display_file_read):
        config = MagicMock(spec=OpenHandsConfig)
        file_read = FileReadObservation(path='test.py', content="print('hello')")

        display_event(file_read, config)

        mock_display_file_read.assert_called_once_with(file_read)

    @patch('openhands.cli.tui.display_message')
    def test_display_event_thought(self, mock_display_message):
        config = MagicMock(spec=OpenHandsConfig)
        action = Action()
        action.thought = 'Thinking about this...'

        display_event(action, config)

        mock_display_message.assert_called_once_with('Thinking about this...')

    @patch('openhands.cli.tui.print_formatted_text')
    def test_display_message(self, mock_print):
        message = 'Test message'
        display_message(message)

        mock_print.assert_called_once()
        args, kwargs = mock_print.call_args
        assert message in str(args[0])

    @patch('openhands.cli.tui.print_container')
    def test_display_command_awaiting_confirmation(self, mock_print_container):
        cmd_action = CmdRunAction(command='echo test')
        cmd_action.confirmation_state = ActionConfirmationStatus.AWAITING_CONFIRMATION

        display_command(cmd_action)

        mock_print_container.assert_called_once()
        container = mock_print_container.call_args[0][0]
        assert 'echo test' in container.body.text


class TestInteractiveCommandFunctions:
    @patch('openhands.cli.tui.print_container')
    def test_display_usage_metrics(self, mock_print_container):
        metrics = UsageMetrics()
        metrics.total_cost = 1.25
        metrics.total_input_tokens = 1000
        metrics.total_output_tokens = 2000

        display_usage_metrics(metrics)

        mock_print_container.assert_called_once()

    def test_get_session_duration(self):
        import time

        current_time = time.time()
        one_hour_ago = current_time - 3600

        # Test for a 1-hour session
        duration = get_session_duration(one_hour_ago)
        assert '1h' in duration
        assert '0m' in duration
        assert '0s' in duration

    @patch('openhands.cli.tui.print_formatted_text')
    @patch('openhands.cli.tui.get_session_duration')
    def test_display_shutdown_message(self, mock_get_duration, mock_print):
        mock_get_duration.return_value = '1 hour 5 minutes'

        metrics = UsageMetrics()
        metrics.total_cost = 1.25
        session_id = 'test-session-id'

        display_shutdown_message(metrics, session_id)

        assert mock_print.call_count >= 3  # At least 3 print calls
        assert mock_get_duration.call_count == 1

    @patch('openhands.cli.tui.display_usage_metrics')
    def test_display_status(self, mock_display_metrics):
        metrics = UsageMetrics()
        session_id = 'test-session-id'

        display_status(metrics, session_id)

        mock_display_metrics.assert_called_once_with(metrics)


class TestCustomDiffLexer:
    def test_custom_diff_lexer_plus_line(self):
        lexer = CustomDiffLexer()
        document = Mock()
        document.lines = ['+added line']

        line_style = lexer.lex_document(document)(0)

        assert line_style[0][0] == 'ansigreen'  # Green for added lines
        assert line_style[0][1] == '+added line'

    def test_custom_diff_lexer_minus_line(self):
        lexer = CustomDiffLexer()
        document = Mock()
        document.lines = ['-removed line']

        line_style = lexer.lex_document(document)(0)

        assert line_style[0][0] == 'ansired'  # Red for removed lines
        assert line_style[0][1] == '-removed line'

    def test_custom_diff_lexer_metadata_line(self):
        lexer = CustomDiffLexer()
        document = Mock()
        document.lines = ['[Existing file]']

        line_style = lexer.lex_document(document)(0)

        assert line_style[0][0] == 'bold'  # Bold for metadata lines
        assert line_style[0][1] == '[Existing file]'

    def test_custom_diff_lexer_normal_line(self):
        lexer = CustomDiffLexer()
        document = Mock()
        document.lines = ['normal line']

        line_style = lexer.lex_document(document)(0)

        assert line_style[0][0] == ''  # Default style for other lines
        assert line_style[0][1] == 'normal line'


class TestUsageMetrics:
    def test_usage_metrics_initialization(self):
        metrics = UsageMetrics()

        # Only test the attributes that are actually initialized
        assert isinstance(metrics.metrics, Metrics)
        assert metrics.session_init_time > 0  # Should have a valid timestamp


class TestUserCancelledError:
    def test_user_cancelled_error(self):
        error = UserCancelledError()
        assert isinstance(error, Exception)


class TestReadConfirmationInput:
    @pytest.mark.asyncio
    @patch('openhands.cli.tui.create_prompt_session')
    async def test_read_confirmation_input_yes(self, mock_create_session):
        mock_session = AsyncMock()
        mock_session.prompt_async.return_value = 'y'
        mock_create_session.return_value = mock_session

        result = await read_confirmation_input(config=MagicMock(spec=OpenHandsConfig))
        assert result == 'yes'

    @pytest.mark.asyncio
    @patch('openhands.cli.tui.create_prompt_session')
    async def test_read_confirmation_input_yes_full(self, mock_create_session):
        mock_session = AsyncMock()
        mock_session.prompt_async.return_value = 'yes'
        mock_create_session.return_value = mock_session

        result = await read_confirmation_input(config=MagicMock(spec=OpenHandsConfig))
        assert result == 'yes'

    @pytest.mark.asyncio
    @patch('openhands.cli.tui.create_prompt_session')
    async def test_read_confirmation_input_no(self, mock_create_session):
        mock_session = AsyncMock()
        mock_session.prompt_async.return_value = 'n'
        mock_create_session.return_value = mock_session

        result = await read_confirmation_input(config=MagicMock(spec=OpenHandsConfig))
        assert result == 'no'

    @pytest.mark.asyncio
    @patch('openhands.cli.tui.create_prompt_session')
    async def test_read_confirmation_input_no_full(self, mock_create_session):
        mock_session = AsyncMock()
        mock_session.prompt_async.return_value = 'no'
        mock_create_session.return_value = mock_session

        result = await read_confirmation_input(config=MagicMock(spec=OpenHandsConfig))
        assert result == 'no'

    @pytest.mark.asyncio
    @patch('openhands.cli.tui.create_prompt_session')
    async def test_read_confirmation_input_always(self, mock_create_session):
        mock_session = AsyncMock()
        mock_session.prompt_async.return_value = 'a'
        mock_create_session.return_value = mock_session

        result = await read_confirmation_input(config=MagicMock(spec=OpenHandsConfig))
        assert result == 'always'

    @pytest.mark.asyncio
    @patch('openhands.cli.tui.create_prompt_session')
    async def test_read_confirmation_input_always_full(self, mock_create_session):
        mock_session = AsyncMock()
        mock_session.prompt_async.return_value = 'always'
        mock_create_session.return_value = mock_session

        result = await read_confirmation_input(config=MagicMock(spec=OpenHandsConfig))
        assert result == 'always'

    @pytest.mark.asyncio
    @patch('openhands.cli.tui.print_formatted_text')
    @patch('openhands.cli.tui.create_prompt_session')
    async def test_read_confirmation_input_invalid_then_valid(
        self, mock_create_session, mock_print
    ):
        mock_session = AsyncMock()
        # First return invalid input, then valid input
        mock_session.prompt_async.side_effect = ['invalid', 'y']
        mock_create_session.return_value = mock_session

        result = await read_confirmation_input(config=MagicMock(spec=OpenHandsConfig))
        assert result == 'yes'

        # Verify error message was displayed
        error_calls = [
            call
            for call in mock_print.call_args_list
            if len(call[0]) > 0 and 'Invalid input' in str(call[0][0])
        ]
        assert len(error_calls) > 0

    @pytest.mark.asyncio
    @patch('openhands.cli.tui.print_formatted_text')
    @patch('openhands.cli.tui.create_prompt_session')
    async def test_read_confirmation_input_empty_then_valid(
        self, mock_create_session, mock_print
    ):
        mock_session = AsyncMock()
        # First return empty input, then valid input
        mock_session.prompt_async.side_effect = ['', 'n']
        mock_create_session.return_value = mock_session

        result = await read_confirmation_input(config=MagicMock(spec=OpenHandsConfig))
        assert result == 'no'

        # Verify error message was displayed
        error_calls = [
            call
            for call in mock_print.call_args_list
            if len(call[0]) > 0 and 'Invalid input' in str(call[0][0])
        ]
        assert len(error_calls) > 0

    @pytest.mark.asyncio
    @patch('openhands.cli.tui.print_formatted_text')
    @patch('openhands.cli.tui.create_prompt_session')
    async def test_read_confirmation_input_none_then_valid(
        self, mock_create_session, mock_print
    ):
        mock_session = AsyncMock()
        # First return None, then valid input
        mock_session.prompt_async.side_effect = [None, 'always']
        mock_create_session.return_value = mock_session

        result = await read_confirmation_input(config=MagicMock(spec=OpenHandsConfig))
        assert result == 'always'

        # Verify error message was displayed
        error_calls = [
            call
            for call in mock_print.call_args_list
            if len(call[0]) > 0 and 'Invalid input' in str(call[0][0])
        ]
        assert len(error_calls) > 0

    @pytest.mark.asyncio
    @patch('openhands.cli.tui.print_formatted_text')
    @patch('openhands.cli.tui.create_prompt_session')
    async def test_read_confirmation_input_multiple_invalid_then_valid(
        self, mock_create_session, mock_print
    ):
        mock_session = AsyncMock()
        # Multiple invalid inputs, then valid input
        mock_session.prompt_async.side_effect = ['invalid1', 'invalid2', 'maybe', 'y']
        mock_create_session.return_value = mock_session

        result = await read_confirmation_input(config=MagicMock(spec=OpenHandsConfig))
        assert result == 'yes'

        # Verify error message was displayed multiple times
        error_calls = [
            call
            for call in mock_print.call_args_list
            if len(call[0]) > 0 and 'Invalid input' in str(call[0][0])
        ]
        assert len(error_calls) >= 3  # Should have at least 3 error messages

    @pytest.mark.asyncio
    @patch('openhands.cli.tui.create_prompt_session')
    async def test_read_confirmation_input_keyboard_interrupt(
        self, mock_create_session
    ):
        mock_session = AsyncMock()
        mock_session.prompt_async.side_effect = KeyboardInterrupt
        mock_create_session.return_value = mock_session

        result = await read_confirmation_input(config=MagicMock(spec=OpenHandsConfig))
        assert result == 'no'

    @pytest.mark.asyncio
    @patch('openhands.cli.tui.create_prompt_session')
    async def test_read_confirmation_input_eof_error(self, mock_create_session):
        mock_session = AsyncMock()
        mock_session.prompt_async.side_effect = EOFError
        mock_create_session.return_value = mock_session

        result = await read_confirmation_input(config=MagicMock(spec=OpenHandsConfig))
        assert result == 'no'
