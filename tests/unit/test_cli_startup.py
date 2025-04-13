import asyncio
from datetime import datetime
from io import StringIO
from unittest.mock import AsyncMock, Mock, patch

import pytest
from prompt_toolkit.application import create_app_session
from prompt_toolkit.input import create_pipe_input
from prompt_toolkit.output import create_output

from openhands.core.cli import main
from openhands.core.config import AppConfig


class MockEventStream:
    def __init__(self):
        self._subscribers = {}
        self.cur_id = 0

    def subscribe(self, subscriber_id, callback, callback_id):
        if subscriber_id not in self._subscribers:
            self._subscribers[subscriber_id] = {}
        self._subscribers[subscriber_id][callback_id] = callback

    def unsubscribe(self, subscriber_id, callback_id):
        if (
            subscriber_id in self._subscribers
            and callback_id in self._subscribers[subscriber_id]
        ):
            del self._subscribers[subscriber_id][callback_id]

    def add_event(self, event, source):
        event._id = self.cur_id
        self.cur_id += 1
        event._source = source
        event._timestamp = datetime.now().isoformat()

        for subscriber_id in self._subscribers:
            for callback_id, callback in self._subscribers[subscriber_id].items():
                callback(event)


@pytest.fixture
def mock_agent():
    with patch('openhands.core.cli.create_agent') as mock_create_agent:
        mock_agent_instance = AsyncMock()
        mock_agent_instance.name = 'test-agent'
        mock_agent_instance.llm = AsyncMock()
        mock_agent_instance.llm.config = AsyncMock()
        mock_agent_instance.llm.config.model = 'test-model'
        mock_agent_instance.llm.config.base_url = 'http://test'
        mock_agent_instance.llm.config.max_message_chars = 1000
        mock_agent_instance.config = AsyncMock()
        mock_agent_instance.config.disabled_microagents = []
        mock_agent_instance.sandbox_plugins = []
        mock_agent_instance.prompt_manager = AsyncMock()
        mock_create_agent.return_value = mock_agent_instance
        yield mock_agent_instance


@pytest.fixture
def mock_controller():
    with patch('openhands.core.cli.create_controller') as mock_create_controller:
        mock_controller_instance = AsyncMock()
        mock_controller_instance.state.agent_state = None
        # Mock run_until_done to finish immediately
        mock_controller_instance.run_until_done = AsyncMock(return_value=None)
        mock_create_controller.return_value = (mock_controller_instance, None)
        yield mock_controller_instance


@pytest.fixture
def mock_config():
    with patch('openhands.core.cli.parse_arguments') as mock_parse_args:
        args = Mock()
        args.file = None
        args.task = None
        args.directory = None
        mock_parse_args.return_value = args
        with patch('openhands.core.cli.setup_config_from_args') as mock_setup_config:
            mock_config = AppConfig()
            mock_config.cli_multiline_input = False
            mock_config.security = Mock()
            mock_config.security.confirmation_mode = False
            mock_config.sandbox = Mock()
            mock_config.sandbox.selected_repo = None
            mock_config.workspace_base = '/test'
            mock_setup_config.return_value = mock_config
            yield mock_config


@pytest.fixture
def mock_memory():
    with patch('openhands.core.cli.create_memory') as mock_create_memory:
        mock_memory_instance = AsyncMock()
        mock_create_memory.return_value = mock_memory_instance
        yield mock_memory_instance


@pytest.fixture
def mock_read_task():
    with patch('openhands.core.cli.read_task') as mock_read_task:
        mock_read_task.return_value = None
        yield mock_read_task


@pytest.fixture
def mock_runtime():
    with patch('openhands.core.cli.create_runtime') as mock_create_runtime:
        mock_runtime_instance = AsyncMock()

        mock_event_stream = MockEventStream()
        mock_runtime_instance.event_stream = mock_event_stream

        mock_runtime_instance.connect = AsyncMock()

        # Ensure status_callback is None
        mock_runtime_instance.status_callback = None
        # Mock get_microagents_from_selected_repo
        mock_runtime_instance.get_microagents_from_selected_repo = Mock(return_value=[])
        mock_create_runtime.return_value = mock_runtime_instance
        yield mock_runtime_instance


@pytest.mark.asyncio
async def test_cli_startup_folder_security_confirmation_agree(
    mock_runtime, mock_controller, mock_config, mock_agent, mock_memory, mock_read_task
):
    buffer = StringIO()

    with patch(
        'openhands.core.cli.manage_openhands_file', return_value=False
    ) as mock_manage_openhands_file:
        with patch(
            'openhands.core.cli.cli_confirm', return_value=True
        ) as mock_cli_confirm:
            with create_app_session(
                input=create_pipe_input(), output=create_output(stdout=buffer)
            ):
                mock_controller.status_callback = None

                main_task = asyncio.create_task(main(asyncio.get_event_loop()))

                await asyncio.sleep(0.1)

                try:
                    await asyncio.wait_for(main_task, timeout=0.1)
                except Exception:
                    main_task.cancel()

                buffer.seek(0)
                output = buffer.read()

                # ASCII art banner
                assert '___' in output

                # Version information
                assert 'OpenHands CLI v' in output

                # Session initialization
                assert 'Initializing session' in output

                # Folder security confirmation
                assert 'Do you trust the files in this folder?' in output
                assert '/test' in output
                assert (
                    'OpenHands may read and execute files in this folder with your permission.'
                    in output
                )

                # Confirmation prompt
                mock_manage_openhands_file.assert_any_call('/test')
                mock_cli_confirm.assert_called_once_with(
                    'Do you wish to continue?', ['Yes, proceed', 'No, exit']
                )
                mock_manage_openhands_file.assert_any_call('/test', add_to_trusted=True)

                # Session initialization complete
                assert 'Initialized session' in output

                # Welcome message
                assert "Let's start building!" in output
                assert 'What do you want to build?' in output
                assert 'Type /help for help' in output


@pytest.mark.asyncio
async def test_cli_startup_folder_security_confirmation_disagree(
    mock_runtime, mock_controller, mock_config, mock_agent, mock_memory, mock_read_task
):
    buffer = StringIO()

    with patch(
        'openhands.core.cli.manage_openhands_file', return_value=False
    ) as mock_manage_openhands_file:
        with patch(
            'openhands.core.cli.cli_confirm', return_value=False
        ) as mock_cli_confirm:
            with create_app_session(
                input=create_pipe_input(), output=create_output(stdout=buffer)
            ):
                mock_controller.status_callback = None

                main_task = asyncio.create_task(main(asyncio.get_event_loop()))

                await asyncio.sleep(0.1)

                try:
                    await asyncio.wait_for(main_task, timeout=0.1)
                except Exception:
                    main_task.cancel()

                buffer.seek(0)
                output = buffer.read()

                # ASCII art banner
                assert '___' in output

                # Version information
                assert 'OpenHands CLI v' in output

                # Session initialization
                assert 'Initializing session' in output

                # Folder security confirmation
                assert 'Do you trust the files in this folder?' in output
                assert '/test' in output
                assert (
                    'OpenHands may read and execute files in this folder with your permission.'
                    in output
                )

                # Confirmation prompt
                mock_manage_openhands_file.assert_called_once_with('/test')
                mock_cli_confirm.assert_called_once_with(
                    'Do you wish to continue?', ['Yes, proceed', 'No, exit']
                )

                # Session initialization complete
                assert 'Initialized session' not in output

                # Welcome message
                assert "Let's start building!" not in output
                assert 'What do you want to build?' not in output
                assert 'Type /help for help' not in output


@pytest.mark.asyncio
async def test_cli_startup_trusted_folder(
    mock_runtime, mock_controller, mock_config, mock_agent, mock_memory, mock_read_task
):
    buffer = StringIO()

    with patch('openhands.core.cli.manage_openhands_file', return_value=True):
        with patch(
            'openhands.core.cli.cli_confirm', return_value=True
        ) as mock_cli_confirm:
            with create_app_session(
                input=create_pipe_input(), output=create_output(stdout=buffer)
            ):
                mock_controller.status_callback = None

                main_task = asyncio.create_task(main(asyncio.get_event_loop()))

                await asyncio.sleep(0.1)

                try:
                    await asyncio.wait_for(main_task, timeout=0.1)
                except Exception:
                    main_task.cancel()

                buffer.seek(0)
                output = buffer.read()

                # ASCII art banner
                assert '___' in output

                # Version information
                assert 'OpenHands CLI v' in output

                # Session initialization
                assert 'Initializing session' in output

                # Folder security confirmation should not be shown
                assert 'Do you trust the files in this folder?' not in output
                assert '/test' not in output
                assert (
                    'OpenHands may read and execute files in this folder with your permission.'
                    not in output
                )

                # Confirmation prompt should not be shown
                mock_cli_confirm.assert_not_called()

                # Session initialization
                assert 'Initialized session' in output

                # Welcome message
                assert "Let's start building!" in output
                assert 'What do you want to build?' in output
                assert 'Type /help for help' in output
