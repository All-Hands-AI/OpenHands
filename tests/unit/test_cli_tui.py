from unittest.mock import MagicMock, Mock, patch

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
)
from openhands.core.config import AppConfig
from openhands.events import EventSource
from openhands.events.action import (
    Action,
    ActionConfirmationStatus,
    CmdRunAction,
    FileEditAction,
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
        assert 'Initialized session' in str(args[0])

    @patch('openhands.cli.tui.print_formatted_text')
    def test_display_welcome_message(self, mock_print):
        display_welcome_message()
        assert mock_print.call_count == 2
        # Check the first call contains the welcome message
        args, kwargs = mock_print.call_args_list[0]
        assert "Let's start building" in str(args[0])

    @patch('openhands.cli.tui.display_message')
    def test_display_event_message_action(self, mock_display_message):
        config = MagicMock(spec=AppConfig)
        message = MessageAction(content='Test message')
        message._source = EventSource.AGENT

        display_event(message, config)

        mock_display_message.assert_called_once_with('Test message')

    @patch('openhands.cli.tui.display_command')
    def test_display_event_cmd_action(self, mock_display_command):
        config = MagicMock(spec=AppConfig)
        cmd_action = CmdRunAction(command='echo test')

        display_event(cmd_action, config)

        mock_display_command.assert_called_once_with(cmd_action)

    @patch('openhands.cli.tui.display_command_output')
    def test_display_event_cmd_output(self, mock_display_output):
        config = MagicMock(spec=AppConfig)
        cmd_output = CmdOutputObservation(content='Test output', command='echo test')

        display_event(cmd_output, config)

        mock_display_output.assert_called_once_with('Test output')

    @patch('openhands.cli.tui.display_file_edit')
    def test_display_event_file_edit_action(self, mock_display_file_edit):
        config = MagicMock(spec=AppConfig)
        file_edit = FileEditAction(path='test.py', content="print('hello')")

        display_event(file_edit, config)

        mock_display_file_edit.assert_called_once_with(file_edit)

    @patch('openhands.cli.tui.display_file_edit')
    def test_display_event_file_edit_observation(self, mock_display_file_edit):
        config = MagicMock(spec=AppConfig)
        file_edit_obs = FileEditObservation(path='test.py', content="print('hello')")

        display_event(file_edit_obs, config)

        mock_display_file_edit.assert_called_once_with(file_edit_obs)

    @patch('openhands.cli.tui.display_file_read')
    def test_display_event_file_read(self, mock_display_file_read):
        config = MagicMock(spec=AppConfig)
        file_read = FileReadObservation(path='test.py', content="print('hello')")

        display_event(file_read, config)

        mock_display_file_read.assert_called_once_with(file_read)

    @patch('openhands.cli.tui.display_message')
    def test_display_event_thought(self, mock_display_message):
        config = MagicMock(spec=AppConfig)
        action = Action()
        action.thought = 'Thinking about this...'

        display_event(action, config)

        mock_display_message.assert_called_once_with('Thinking about this...')

    @patch('openhands.cli.tui.time.sleep')
    @patch('openhands.cli.tui.print_formatted_text')
    def test_display_message(self, mock_print, mock_sleep):
        message = 'Test message'
        display_message(message)

        mock_sleep.assert_called_once_with(0.2)
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
