from unittest.mock import MagicMock, patch

import pytest

from openhands.cli.commands import (
    handle_commands,
    handle_exit_command,
    handle_help_command,
    handle_init_command,
    handle_new_command,
    handle_resume_command,
    handle_settings_command,
    handle_status_command,
)
from openhands.cli.tui import UsageMetrics
from openhands.core.config import OpenHandsConfig
from openhands.core.schema import AgentState
from openhands.events import EventSource
from openhands.events.action import ChangeAgentStateAction, MessageAction
from openhands.events.stream import EventStream
from openhands.storage.settings.file_settings_store import FileSettingsStore


class TestHandleCommands:
    @pytest.fixture
    def mock_dependencies(self):
        event_stream = MagicMock(spec=EventStream)
        usage_metrics = MagicMock(spec=UsageMetrics)
        sid = 'test-session-id'
        config = MagicMock(spec=OpenHandsConfig)
        current_dir = '/test/dir'
        settings_store = MagicMock(spec=FileSettingsStore)

        return {
            'event_stream': event_stream,
            'usage_metrics': usage_metrics,
            'sid': sid,
            'config': config,
            'current_dir': current_dir,
            'settings_store': settings_store,
        }

    @pytest.mark.asyncio
    @patch('openhands.cli.commands.handle_exit_command')
    async def test_handle_exit_command(self, mock_handle_exit, mock_dependencies):
        mock_handle_exit.return_value = True

        close_repl, reload_microagents, new_session = await handle_commands(
            '/exit', **mock_dependencies
        )

        mock_handle_exit.assert_called_once_with(
            mock_dependencies['event_stream'],
            mock_dependencies['usage_metrics'],
            mock_dependencies['sid'],
        )
        assert close_repl is True
        assert reload_microagents is False
        assert new_session is False

    @pytest.mark.asyncio
    @patch('openhands.cli.commands.handle_help_command')
    async def test_handle_help_command(self, mock_handle_help, mock_dependencies):
        mock_handle_help.return_value = (False, False, False)

        close_repl, reload_microagents, new_session = await handle_commands(
            '/help', **mock_dependencies
        )

        mock_handle_help.assert_called_once()
        assert close_repl is False
        assert reload_microagents is False
        assert new_session is False

    @pytest.mark.asyncio
    @patch('openhands.cli.commands.handle_init_command')
    async def test_handle_init_command(self, mock_handle_init, mock_dependencies):
        mock_handle_init.return_value = (True, True)

        close_repl, reload_microagents, new_session = await handle_commands(
            '/init', **mock_dependencies
        )

        mock_handle_init.assert_called_once_with(
            mock_dependencies['config'],
            mock_dependencies['event_stream'],
            mock_dependencies['current_dir'],
        )
        assert close_repl is True
        assert reload_microagents is True
        assert new_session is False

    @pytest.mark.asyncio
    @patch('openhands.cli.commands.handle_status_command')
    async def test_handle_status_command(self, mock_handle_status, mock_dependencies):
        mock_handle_status.return_value = (False, False, False)

        close_repl, reload_microagents, new_session = await handle_commands(
            '/status', **mock_dependencies
        )

        mock_handle_status.assert_called_once_with(
            mock_dependencies['usage_metrics'], mock_dependencies['sid']
        )
        assert close_repl is False
        assert reload_microagents is False
        assert new_session is False

    @pytest.mark.asyncio
    @patch('openhands.cli.commands.handle_new_command')
    async def test_handle_new_command(self, mock_handle_new, mock_dependencies):
        mock_handle_new.return_value = (True, True)

        close_repl, reload_microagents, new_session = await handle_commands(
            '/new', **mock_dependencies
        )

        mock_handle_new.assert_called_once_with(
            mock_dependencies['event_stream'],
            mock_dependencies['usage_metrics'],
            mock_dependencies['sid'],
        )
        assert close_repl is True
        assert reload_microagents is False
        assert new_session is True

    @pytest.mark.asyncio
    @patch('openhands.cli.commands.handle_settings_command')
    async def test_handle_settings_command(
        self, mock_handle_settings, mock_dependencies
    ):
        close_repl, reload_microagents, new_session = await handle_commands(
            '/settings', **mock_dependencies
        )

        mock_handle_settings.assert_called_once_with(
            mock_dependencies['config'],
            mock_dependencies['settings_store'],
        )
        assert close_repl is False
        assert reload_microagents is False
        assert new_session is False

    @pytest.mark.asyncio
    async def test_handle_unknown_command(self, mock_dependencies):
        user_message = 'Hello, this is not a command'

        close_repl, reload_microagents, new_session = await handle_commands(
            user_message, **mock_dependencies
        )

        # The command should be treated as a message and added to the event stream
        mock_dependencies['event_stream'].add_event.assert_called_once()
        # Check the first argument is a MessageAction with the right content
        args, kwargs = mock_dependencies['event_stream'].add_event.call_args
        assert isinstance(args[0], MessageAction)
        assert args[0].content == user_message
        assert args[1] == EventSource.USER

        assert close_repl is True
        assert reload_microagents is False
        assert new_session is False


class TestHandleExitCommand:
    @patch('openhands.cli.commands.cli_confirm')
    @patch('openhands.cli.commands.display_shutdown_message')
    def test_exit_with_confirmation(self, mock_display_shutdown, mock_cli_confirm):
        event_stream = MagicMock(spec=EventStream)
        usage_metrics = MagicMock(spec=UsageMetrics)
        sid = 'test-session-id'

        # Mock user confirming exit
        mock_cli_confirm.return_value = 0  # First option, which is "Yes, proceed"

        # Call the function under test
        result = handle_exit_command(event_stream, usage_metrics, sid)

        # Verify correct behavior
        mock_cli_confirm.assert_called_once()
        event_stream.add_event.assert_called_once()
        # Check event is the right type
        args, kwargs = event_stream.add_event.call_args
        assert isinstance(args[0], ChangeAgentStateAction)
        assert args[0].agent_state == AgentState.STOPPED
        assert args[1] == EventSource.ENVIRONMENT

        mock_display_shutdown.assert_called_once_with(usage_metrics, sid)
        assert result is True

    @patch('openhands.cli.commands.cli_confirm')
    @patch('openhands.cli.commands.display_shutdown_message')
    def test_exit_without_confirmation(self, mock_display_shutdown, mock_cli_confirm):
        event_stream = MagicMock(spec=EventStream)
        usage_metrics = MagicMock(spec=UsageMetrics)
        sid = 'test-session-id'

        # Mock user rejecting exit
        mock_cli_confirm.return_value = 1  # Second option, which is "No, dismiss"

        # Call the function under test
        result = handle_exit_command(event_stream, usage_metrics, sid)

        # Verify correct behavior
        mock_cli_confirm.assert_called_once()
        event_stream.add_event.assert_not_called()
        mock_display_shutdown.assert_not_called()
        assert result is False


class TestHandleHelpCommand:
    @patch('openhands.cli.commands.display_help')
    def test_help_command(self, mock_display_help):
        handle_help_command()
        mock_display_help.assert_called_once()


class TestHandleStatusCommand:
    @patch('openhands.cli.commands.display_status')
    def test_status_command(self, mock_display_status):
        usage_metrics = MagicMock(spec=UsageMetrics)
        sid = 'test-session-id'

        handle_status_command(usage_metrics, sid)

        mock_display_status.assert_called_once_with(usage_metrics, sid)


class TestHandleNewCommand:
    @patch('openhands.cli.commands.cli_confirm')
    @patch('openhands.cli.commands.display_shutdown_message')
    def test_new_with_confirmation(self, mock_display_shutdown, mock_cli_confirm):
        event_stream = MagicMock(spec=EventStream)
        usage_metrics = MagicMock(spec=UsageMetrics)
        sid = 'test-session-id'

        # Mock user confirming new session
        mock_cli_confirm.return_value = 0  # First option, which is "Yes, proceed"

        # Call the function under test
        close_repl, new_session = handle_new_command(event_stream, usage_metrics, sid)

        # Verify correct behavior
        mock_cli_confirm.assert_called_once()
        event_stream.add_event.assert_called_once()
        # Check event is the right type
        args, kwargs = event_stream.add_event.call_args
        assert isinstance(args[0], ChangeAgentStateAction)
        assert args[0].agent_state == AgentState.STOPPED
        assert args[1] == EventSource.ENVIRONMENT

        mock_display_shutdown.assert_called_once_with(usage_metrics, sid)
        assert close_repl is True
        assert new_session is True

    @patch('openhands.cli.commands.cli_confirm')
    @patch('openhands.cli.commands.display_shutdown_message')
    def test_new_without_confirmation(self, mock_display_shutdown, mock_cli_confirm):
        event_stream = MagicMock(spec=EventStream)
        usage_metrics = MagicMock(spec=UsageMetrics)
        sid = 'test-session-id'

        # Mock user rejecting new session
        mock_cli_confirm.return_value = 1  # Second option, which is "No, dismiss"

        # Call the function under test
        close_repl, new_session = handle_new_command(event_stream, usage_metrics, sid)

        # Verify correct behavior
        mock_cli_confirm.assert_called_once()
        event_stream.add_event.assert_not_called()
        mock_display_shutdown.assert_not_called()
        assert close_repl is False
        assert new_session is False


class TestHandleInitCommand:
    @pytest.mark.asyncio
    @patch('openhands.cli.commands.init_repository')
    async def test_init_local_runtime_successful(self, mock_init_repository):
        config = MagicMock(spec=OpenHandsConfig)
        config.runtime = 'local'
        event_stream = MagicMock(spec=EventStream)
        current_dir = '/test/dir'

        # Mock successful repository initialization
        mock_init_repository.return_value = True

        # Call the function under test
        close_repl, reload_microagents = await handle_init_command(
            config, event_stream, current_dir
        )

        # Verify correct behavior
        mock_init_repository.assert_called_once_with(current_dir)
        event_stream.add_event.assert_called_once()
        # Check event is the right type
        args, kwargs = event_stream.add_event.call_args
        assert isinstance(args[0], MessageAction)
        assert 'Please explore this repository' in args[0].content
        assert args[1] == EventSource.USER

        assert close_repl is True
        assert reload_microagents is True

    @pytest.mark.asyncio
    @patch('openhands.cli.commands.init_repository')
    async def test_init_local_runtime_unsuccessful(self, mock_init_repository):
        config = MagicMock(spec=OpenHandsConfig)
        config.runtime = 'local'
        event_stream = MagicMock(spec=EventStream)
        current_dir = '/test/dir'

        # Mock unsuccessful repository initialization
        mock_init_repository.return_value = False

        # Call the function under test
        close_repl, reload_microagents = await handle_init_command(
            config, event_stream, current_dir
        )

        # Verify correct behavior
        mock_init_repository.assert_called_once_with(current_dir)
        event_stream.add_event.assert_not_called()

        assert close_repl is False
        assert reload_microagents is False

    @pytest.mark.asyncio
    @patch('openhands.cli.commands.print_formatted_text')
    @patch('openhands.cli.commands.init_repository')
    async def test_init_non_local_runtime(self, mock_init_repository, mock_print):
        config = MagicMock(spec=OpenHandsConfig)
        config.runtime = 'remote'  # Not local
        event_stream = MagicMock(spec=EventStream)
        current_dir = '/test/dir'

        # Call the function under test
        close_repl, reload_microagents = await handle_init_command(
            config, event_stream, current_dir
        )

        # Verify correct behavior
        mock_init_repository.assert_not_called()
        mock_print.assert_called_once()
        event_stream.add_event.assert_not_called()

        assert close_repl is False
        assert reload_microagents is False


class TestHandleSettingsCommand:
    @pytest.mark.asyncio
    @patch('openhands.cli.commands.display_settings')
    @patch('openhands.cli.commands.cli_confirm')
    @patch('openhands.cli.commands.modify_llm_settings_basic')
    async def test_settings_basic_with_changes(
        self,
        mock_modify_basic,
        mock_cli_confirm,
        mock_display_settings,
    ):
        config = MagicMock(spec=OpenHandsConfig)
        settings_store = MagicMock(spec=FileSettingsStore)

        # Mock user selecting "Basic" settings
        mock_cli_confirm.return_value = 0

        # Call the function under test
        await handle_settings_command(config, settings_store)

        # Verify correct behavior
        mock_display_settings.assert_called_once_with(config)
        mock_cli_confirm.assert_called_once()
        mock_modify_basic.assert_called_once_with(config, settings_store)

    @pytest.mark.asyncio
    @patch('openhands.cli.commands.display_settings')
    @patch('openhands.cli.commands.cli_confirm')
    @patch('openhands.cli.commands.modify_llm_settings_basic')
    async def test_settings_basic_without_changes(
        self,
        mock_modify_basic,
        mock_cli_confirm,
        mock_display_settings,
    ):
        config = MagicMock(spec=OpenHandsConfig)
        settings_store = MagicMock(spec=FileSettingsStore)

        # Mock user selecting "Basic" settings
        mock_cli_confirm.return_value = 0

        # Call the function under test
        await handle_settings_command(config, settings_store)

        # Verify correct behavior
        mock_display_settings.assert_called_once_with(config)
        mock_cli_confirm.assert_called_once()
        mock_modify_basic.assert_called_once_with(config, settings_store)

    @pytest.mark.asyncio
    @patch('openhands.cli.commands.display_settings')
    @patch('openhands.cli.commands.cli_confirm')
    @patch('openhands.cli.commands.modify_llm_settings_advanced')
    async def test_settings_advanced_with_changes(
        self,
        mock_modify_advanced,
        mock_cli_confirm,
        mock_display_settings,
    ):
        config = MagicMock(spec=OpenHandsConfig)
        settings_store = MagicMock(spec=FileSettingsStore)

        # Mock user selecting "Advanced" settings
        mock_cli_confirm.return_value = 1

        # Call the function under test
        await handle_settings_command(config, settings_store)

        # Verify correct behavior
        mock_display_settings.assert_called_once_with(config)
        mock_cli_confirm.assert_called_once()
        mock_modify_advanced.assert_called_once_with(config, settings_store)

    @pytest.mark.asyncio
    @patch('openhands.cli.commands.display_settings')
    @patch('openhands.cli.commands.cli_confirm')
    @patch('openhands.cli.commands.modify_llm_settings_advanced')
    async def test_settings_advanced_without_changes(
        self,
        mock_modify_advanced,
        mock_cli_confirm,
        mock_display_settings,
    ):
        config = MagicMock(spec=OpenHandsConfig)
        settings_store = MagicMock(spec=FileSettingsStore)

        # Mock user selecting "Advanced" settings
        mock_cli_confirm.return_value = 1

        # Call the function under test
        await handle_settings_command(config, settings_store)

        # Verify correct behavior
        mock_display_settings.assert_called_once_with(config)
        mock_cli_confirm.assert_called_once()
        mock_modify_advanced.assert_called_once_with(config, settings_store)

    @pytest.mark.asyncio
    @patch('openhands.cli.commands.display_settings')
    @patch('openhands.cli.commands.cli_confirm')
    async def test_settings_go_back(self, mock_cli_confirm, mock_display_settings):
        config = MagicMock(spec=OpenHandsConfig)
        settings_store = MagicMock(spec=FileSettingsStore)

        # Mock user selecting "Go back"
        mock_cli_confirm.return_value = 2

        # Call the function under test
        await handle_settings_command(config, settings_store)

        # Verify correct behavior
        mock_display_settings.assert_called_once_with(config)
        mock_cli_confirm.assert_called_once()


class TestHandleResumeCommand:
    @pytest.mark.asyncio
    async def test_handle_resume_command(self):
        """Test that handle_resume_command adds the 'continue' message to the event stream."""
        # Create a mock event stream
        event_stream = MagicMock(spec=EventStream)

        # Call the function
        close_repl, new_session_requested = await handle_resume_command(event_stream)

        # Check that the event stream add_event was called with the correct message action
        event_stream.add_event.assert_called_once()
        args, kwargs = event_stream.add_event.call_args
        message_action, source = args

        assert isinstance(message_action, MessageAction)
        assert message_action.content == 'continue'
        assert source == EventSource.USER

        # Check the return values
        assert close_repl is True
        assert new_session_requested is False
