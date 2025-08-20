from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from prompt_toolkit.formatted_text import HTML

from openhands.cli.commands import (
    display_mcp_servers,
    get_initial_user_message,
    handle_commands,
    handle_conv_command,
    handle_exit_command,
    handle_help_command,
    handle_init_command,
    handle_mcp_command,
    handle_new_command,
    handle_resume_command,
    handle_settings_command,
    handle_status_command,
    list_conversations,
    truncate_message,
    view_conversation_details,
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
        agent_state = AgentState.RUNNING

        return {
            'event_stream': event_stream,
            'usage_metrics': usage_metrics,
            'sid': sid,
            'config': config,
            'current_dir': current_dir,
            'settings_store': settings_store,
            'agent_state': agent_state,
        }

    @pytest.mark.asyncio
    @patch('openhands.cli.commands.handle_exit_command')
    async def test_handle_exit_command(self, mock_handle_exit, mock_dependencies):
        mock_handle_exit.return_value = True

        close_repl, reload_microagents, new_session, _ = await handle_commands(
            '/exit', **mock_dependencies
        )

        mock_handle_exit.assert_called_once_with(
            mock_dependencies['config'],
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

        close_repl, reload_microagents, new_session, _ = await handle_commands(
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

        close_repl, reload_microagents, new_session, _ = await handle_commands(
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

        close_repl, reload_microagents, new_session, _ = await handle_commands(
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

        close_repl, reload_microagents, new_session, _ = await handle_commands(
            '/new', **mock_dependencies
        )

        mock_handle_new.assert_called_once_with(
            mock_dependencies['config'],
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
        close_repl, reload_microagents, new_session, _ = await handle_commands(
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
    @patch('openhands.cli.commands.handle_mcp_command')
    async def test_handle_mcp_command(self, mock_handle_mcp, mock_dependencies):
        close_repl, reload_microagents, new_session, _ = await handle_commands(
            '/mcp', **mock_dependencies
        )

        mock_handle_mcp.assert_called_once_with(mock_dependencies['config'])
        assert close_repl is False
        assert reload_microagents is False
        assert new_session is False

    @pytest.mark.asyncio
    @patch('openhands.cli.commands.handle_conv_command')
    async def test_handle_conv_command(self, mock_handle_conv, mock_dependencies):
        close_repl, reload_microagents, new_session, _ = await handle_commands(
            '/conv', **mock_dependencies
        )

        mock_handle_conv.assert_called_once_with(mock_dependencies['config'])
        assert close_repl is False
        assert reload_microagents is False
        assert new_session is False

    @pytest.mark.asyncio
    async def test_handle_unknown_command(self, mock_dependencies):
        user_message = 'Hello, this is not a command'

        close_repl, reload_microagents, new_session, _ = await handle_commands(
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
        config = MagicMock(spec=OpenHandsConfig)
        event_stream = MagicMock(spec=EventStream)
        usage_metrics = MagicMock(spec=UsageMetrics)
        sid = 'test-session-id'

        # Mock user confirming exit
        mock_cli_confirm.return_value = 0  # First option, which is "Yes, proceed"

        # Call the function under test
        result = handle_exit_command(config, event_stream, usage_metrics, sid)

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
        config = MagicMock(spec=OpenHandsConfig)
        event_stream = MagicMock(spec=EventStream)
        usage_metrics = MagicMock(spec=UsageMetrics)
        sid = 'test-session-id'

        # Mock user rejecting exit
        mock_cli_confirm.return_value = 1  # Second option, which is "No, dismiss"

        # Call the function under test
        result = handle_exit_command(config, event_stream, usage_metrics, sid)

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


class TestDisplayMcpServers:
    @patch('openhands.cli.commands.print_formatted_text')
    def test_display_mcp_servers_no_servers(self, mock_print):
        from openhands.core.config.mcp_config import MCPConfig

        config = MagicMock(spec=OpenHandsConfig)
        config.mcp = MCPConfig()  # Empty config with no servers

        display_mcp_servers(config)

        mock_print.assert_called_once()
        call_args = mock_print.call_args[0][0]
        assert 'No custom MCP servers configured' in call_args
        assert (
            'https://docs.all-hands.dev/usage/how-to/cli-mode#using-mcp-servers'
            in call_args
        )

    @patch('openhands.cli.commands.print_formatted_text')
    def test_display_mcp_servers_with_servers(self, mock_print):
        from openhands.core.config.mcp_config import (
            MCPConfig,
            MCPSHTTPServerConfig,
            MCPSSEServerConfig,
            MCPStdioServerConfig,
        )

        config = MagicMock(spec=OpenHandsConfig)
        config.mcp = MCPConfig(
            sse_servers=[MCPSSEServerConfig(url='https://example.com/sse')],
            stdio_servers=[MCPStdioServerConfig(name='tavily', command='npx')],
            shttp_servers=[MCPSHTTPServerConfig(url='http://localhost:3000/mcp')],
        )

        display_mcp_servers(config)

        # Should be called multiple times for different sections
        assert mock_print.call_count >= 4

        # Check that the summary is printed
        first_call = mock_print.call_args_list[0][0][0]
        assert 'Configured MCP servers:' in first_call
        assert 'SSE servers: 1' in first_call
        assert 'Stdio servers: 1' in first_call
        assert 'SHTTP servers: 1' in first_call
        assert 'Total: 3' in first_call


class TestHandleMcpCommand:
    @pytest.mark.asyncio
    @patch('openhands.cli.commands.cli_confirm')
    @patch('openhands.cli.commands.display_mcp_servers')
    async def test_handle_mcp_command_list_action(self, mock_display, mock_cli_confirm):
        config = MagicMock(spec=OpenHandsConfig)
        mock_cli_confirm.return_value = 0  # List action

        await handle_mcp_command(config)

        mock_cli_confirm.assert_called_once_with(
            config,
            'MCP Server Configuration',
            [
                'List configured servers',
                'Add new server',
                'Remove server',
                'View errors',
                'Go back',
            ],
        )
        mock_display.assert_called_once_with(config)


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
        config = MagicMock(spec=OpenHandsConfig)
        event_stream = MagicMock(spec=EventStream)
        usage_metrics = MagicMock(spec=UsageMetrics)
        sid = 'test-session-id'

        # Mock user confirming new session
        mock_cli_confirm.return_value = 0  # First option, which is "Yes, proceed"

        # Call the function under test
        close_repl, new_session = handle_new_command(
            config, event_stream, usage_metrics, sid
        )

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
        config = MagicMock(spec=OpenHandsConfig)
        event_stream = MagicMock(spec=EventStream)
        usage_metrics = MagicMock(spec=UsageMetrics)
        sid = 'test-session-id'

        # Mock user rejecting new session
        mock_cli_confirm.return_value = 1  # Second option, which is "No, dismiss"

        # Call the function under test
        close_repl, new_session = handle_new_command(
            config, event_stream, usage_metrics, sid
        )

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
        mock_init_repository.assert_called_once_with(config, current_dir)
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
        mock_init_repository.assert_called_once_with(config, current_dir)
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

        # Mock user selecting "Go back" (now option 4, index 3)
        mock_cli_confirm.return_value = 3

        # Call the function under test
        await handle_settings_command(config, settings_store)

        # Verify correct behavior
        mock_display_settings.assert_called_once_with(config)
        mock_cli_confirm.assert_called_once()


class TestHandleResumeCommand:
    @pytest.mark.asyncio
    @patch('openhands.cli.commands.print_formatted_text')
    async def test_handle_resume_command_paused_state(self, mock_print):
        """Test that handle_resume_command works when agent is in PAUSED state."""
        # Create a mock event stream
        event_stream = MagicMock(spec=EventStream)

        # Call the function with PAUSED state
        close_repl, new_session_requested = await handle_resume_command(
            event_stream, AgentState.PAUSED
        )

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

        # Verify no error message was printed
        mock_print.assert_not_called()

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        'invalid_state', [AgentState.RUNNING, AgentState.FINISHED, AgentState.ERROR]
    )
    @patch('openhands.cli.commands.print_formatted_text')
    async def test_handle_resume_command_invalid_states(
        self, mock_print, invalid_state
    ):
        """Test that handle_resume_command shows error for all non-PAUSED states."""
        event_stream = MagicMock(spec=EventStream)

        close_repl, new_session_requested = await handle_resume_command(
            event_stream, invalid_state
        )

        # Check that no event was added to the stream
        event_stream.add_event.assert_not_called()

        # Verify print was called with the error message
        assert mock_print.call_count == 1
        error_call = mock_print.call_args_list[0][0][0]
        assert isinstance(error_call, HTML)
        assert 'Error: Agent is not paused' in str(error_call)
        assert '/resume command is only available when agent is paused' in str(
            error_call
        )

        # Check the return values
        assert close_repl is False
        assert new_session_requested is False


class TestMCPErrorHandling:
    """Test MCP error handling in commands."""

    @patch('openhands.cli.commands.display_mcp_errors')
    def test_handle_mcp_errors_command(self, mock_display_errors):
        """Test handling MCP errors command."""
        from openhands.cli.commands import handle_mcp_errors_command

        handle_mcp_errors_command()

        mock_display_errors.assert_called_once()


class TestConversationCommands:
    """Test conversation history commands."""

    @pytest.mark.asyncio
    @patch('openhands.cli.commands.cli_confirm')
    @patch('openhands.cli.commands.list_conversations')
    async def test_handle_conv_command_list_action(
        self, mock_list_conversations, mock_cli_confirm
    ):
        """Test handle_conv_command with list action."""
        config = MagicMock(spec=OpenHandsConfig)
        mock_cli_confirm.return_value = 0  # List action

        await handle_conv_command(config)

        mock_cli_confirm.assert_called_once_with(
            config,
            'Conversation History',
            [
                'List recent conversations',
                'View conversation details',
                'Go back',
            ],
        )
        mock_list_conversations.assert_called_once_with(config)

    @pytest.mark.asyncio
    @patch('openhands.cli.commands.cli_confirm')
    @patch('openhands.cli.commands.view_conversation_details')
    async def test_handle_conv_command_view_action(
        self, mock_view_details, mock_cli_confirm
    ):
        """Test handle_conv_command with view details action."""
        config = MagicMock(spec=OpenHandsConfig)
        mock_cli_confirm.return_value = 1  # View details action

        await handle_conv_command(config)

        mock_cli_confirm.assert_called_once_with(
            config,
            'Conversation History',
            [
                'List recent conversations',
                'View conversation details',
                'Go back',
            ],
        )
        mock_view_details.assert_called_once_with(config)

    @pytest.mark.asyncio
    @patch('openhands.cli.commands.cli_confirm')
    async def test_handle_conv_command_go_back(self, mock_cli_confirm):
        """Test handle_conv_command with go back action."""
        config = MagicMock(spec=OpenHandsConfig)
        mock_cli_confirm.return_value = 2  # Go back action

        await handle_conv_command(config)

        mock_cli_confirm.assert_called_once()
        # No other functions should be called

    @pytest.mark.asyncio
    @patch('openhands.cli.commands.FileConversationStore.get_instance')
    @patch('openhands.cli.commands.get_initial_user_message')
    @patch('openhands.cli.commands.print_formatted_text')
    async def test_list_conversations_success(
        self, mock_print, mock_get_message, mock_get_instance
    ):
        """Test list_conversations with successful data retrieval."""
        from openhands.storage.data_models.conversation_metadata import (
            ConversationMetadata,
        )
        from openhands.storage.data_models.conversation_metadata_result_set import (
            ConversationMetadataResultSet,
        )

        config = MagicMock(spec=OpenHandsConfig)

        # Mock conversation data
        conv1 = ConversationMetadata(
            conversation_id='conv-1',
            selected_repository='test-repo-1',
            created_at='2023-01-01T10:00:00Z',
            title='Test Conversation 1',
        )
        conv2 = ConversationMetadata(
            conversation_id='conv-2',
            selected_repository='test-repo-2',
            created_at='2023-01-01T11:00:00Z',
            title='Test Conversation 2',
        )

        result_set = ConversationMetadataResultSet([conv1, conv2])

        mock_store = MagicMock()
        mock_store.search = AsyncMock(return_value=result_set)
        mock_get_instance.return_value = mock_store

        mock_get_message.side_effect = ['Hello world', 'Fix this bug']

        await list_conversations(config)

        mock_get_instance.assert_called_once_with(config, None)
        mock_store.search.assert_called_once_with(page_id=None, limit=10)
        assert mock_get_message.call_count == 2
        assert mock_print.call_count >= 4  # Header, separator, conversations, separator

    @pytest.mark.asyncio
    @patch('openhands.cli.commands.FileConversationStore.get_instance')
    @patch('openhands.cli.commands.print_formatted_text')
    async def test_list_conversations_no_conversations(
        self, mock_print, mock_get_instance
    ):
        """Test list_conversations with no conversations found."""
        from openhands.storage.data_models.conversation_metadata_result_set import (
            ConversationMetadataResultSet,
        )

        config = MagicMock(spec=OpenHandsConfig)

        result_set = ConversationMetadataResultSet([])

        mock_store = MagicMock()
        mock_store.search = AsyncMock(return_value=result_set)
        mock_get_instance.return_value = mock_store

        await list_conversations(config)

        mock_print.assert_called_once_with('No conversations found.')

    @pytest.mark.asyncio
    @patch('openhands.cli.commands.collect_input')
    @patch('openhands.cli.commands.get_user_messages_from_conversation')
    @patch('openhands.cli.commands.print_formatted_text')
    async def test_view_conversation_details_success(
        self, mock_print, mock_get_messages, mock_collect_input
    ):
        """Test view_conversation_details with successful data retrieval."""
        config = MagicMock(spec=OpenHandsConfig)
        mock_collect_input.return_value = 'conv-123'
        mock_get_messages.return_value = [
            {'timestamp': '2023-01-01T10:00:00Z', 'content': 'Hello'},
            {'timestamp': '2023-01-01T10:05:00Z', 'content': 'How are you?'},
        ]

        await view_conversation_details(config)

        mock_collect_input.assert_called_once_with(config, 'Enter conversation ID:')
        mock_get_messages.assert_called_once_with(config, 'conv-123')
        assert mock_print.call_count >= 4  # Header, separator, messages, separator

    @pytest.mark.asyncio
    @patch('openhands.cli.commands.collect_input')
    async def test_view_conversation_details_cancelled(self, mock_collect_input):
        """Test view_conversation_details when user cancels input."""
        config = MagicMock(spec=OpenHandsConfig)
        mock_collect_input.return_value = None  # User cancelled

        await view_conversation_details(config)

        mock_collect_input.assert_called_once_with(config, 'Enter conversation ID:')
        # No other functions should be called

    @pytest.mark.asyncio
    async def test_get_initial_user_message_success(self):
        """Test get_initial_user_message with successful message retrieval."""
        # This is more of an integration test - we'll just test that the function
        # handles the case where no message is found gracefully
        config = MagicMock(spec=OpenHandsConfig)
        config.file_store = 'local'
        config.file_store_path = '/tmp/test'
        conversation_id = 'conv-123'

        result = await get_initial_user_message(config, conversation_id)

        # Since we don't have actual conversation data, it should return the error message
        assert result in ['No initial message found', 'Error loading message']

    @pytest.mark.asyncio
    @patch('openhands.storage.get_file_store')
    async def test_get_initial_user_message_error(self, mock_get_file_store):
        """Test get_initial_user_message with error handling."""
        config = MagicMock(spec=OpenHandsConfig)
        conversation_id = 'conv-123'

        mock_get_file_store.side_effect = Exception('File not found')

        result = await get_initial_user_message(config, conversation_id)

        assert result == 'Error loading message'

    def test_truncate_message_short(self):
        """Test truncate_message with short message."""
        message = 'Hello world'
        result = truncate_message(message, 100)
        assert result == 'Hello world'

    def test_truncate_message_long(self):
        """Test truncate_message with long message."""
        message = 'This is a very long message that should be truncated'
        result = truncate_message(message, 20)
        assert result == 'This is a very long ...'
        assert len(result) == 23  # 20 + '...'
