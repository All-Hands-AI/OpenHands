import asyncio
from io import StringIO
from unittest.mock import AsyncMock, Mock, patch, ANY

import pytest
from prompt_toolkit.application import create_app_session
from prompt_toolkit.input import create_pipe_input
from prompt_toolkit.output import create_output

from openhands.core.cli import main, run_session
from openhands.core.config import AppConfig, LLMConfig
from openhands.core.schema import AgentState
from openhands.events.action import ChangeAgentStateAction, MessageAction
from openhands.events.event import EventSource
from openhands.events.observation import AgentStateChangedObservation

class MockEventStream:
    def __init__(self):
        self._subscribers = {}
        self.cur_id = 0
        self.events = []

    def subscribe(self, subscriber_id, callback, callback_id=None):
        if subscriber_id not in self._subscribers:
            self._subscribers[subscriber_id] = {}
        self._subscribers[subscriber_id][callback_id] = callback
        return callback_id

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
        event._timestamp = '2023-01-01T00:00:00'
        self.events.append((event, source))

        for subscriber_id in self._subscribers:
            for callback_id, callback in self._subscribers[subscriber_id].items():
                if asyncio.iscoroutinefunction(callback):
                    asyncio.create_task(callback(event))
                else:
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
        mock_agent_instance.set_mcp_tools = Mock(return_value=None)
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
            mock_config.runtime = 'local'  # Important for /init test
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
async def test_help_command(
    mock_runtime, mock_controller, mock_config, mock_agent, mock_memory, mock_read_task
):
    buffer = StringIO()

    with patch('openhands.core.cli.manage_openhands_file', return_value=True):
        with patch(
            'openhands.core.cli.check_folder_security_agreement', return_value=True
        ):
            with patch('openhands.core.cli.read_prompt_input') as mock_prompt:
                # Setup to return /help first, then simulate an exit
                mock_prompt.side_effect = ['/help', '/exit']

                with create_app_session(
                    input=create_pipe_input(), output=create_output(stdout=buffer)
                ):
                    mock_controller.status_callback = None

                    main_task = asyncio.create_task(main(asyncio.get_event_loop()))

                    agent_ready_event = AgentStateChangedObservation(
                        agent_state=AgentState.AWAITING_USER_INPUT,
                        content='Agent is ready for user input',
                    )
                    mock_runtime.event_stream.add_event(
                        agent_ready_event, EventSource.AGENT
                    )

                    await asyncio.sleep(0.1)

                    try:
                        await asyncio.wait_for(main_task, timeout=0.5)
                    except asyncio.TimeoutError:
                        main_task.cancel()
                        try:
                            await main_task
                        except asyncio.CancelledError:
                            pass

                    buffer.seek(0)
                    output = buffer.read()

                    # Verify help output was displayed
                    assert 'OpenHands CLI' in output
                    assert 'Things that you can try' in output
                    assert 'Interactive commands' in output
                    assert '/help' in output
                    assert '/exit' in output

                    # Verify the help command didn't add a MessageAction to the event stream
                    message_actions = [
                        event
                        for event, _ in mock_runtime.event_stream.events
                        if isinstance(event, MessageAction)
                    ]
                    assert len(message_actions) == 0


@pytest.mark.asyncio
async def test_exit_command(
    mock_runtime, mock_controller, mock_config, mock_agent, mock_memory, mock_read_task
):
    buffer = StringIO()

    with patch('openhands.core.cli.manage_openhands_file', return_value=True), \
        patch('openhands.core.cli.cli_confirm', return_value=0):
        with patch(
            'openhands.core.cli.check_folder_security_agreement', return_value=True
        ):
            with patch('openhands.core.cli.read_prompt_input') as mock_prompt:
                # First prompt call returns /exit
                mock_prompt.side_effect = ['/exit']

                with patch('openhands.core.cli.display_shutdown_message') as mock_shutdown:
                    with create_app_session(
                        input=create_pipe_input(), output=create_output(stdout=buffer)
                    ):
                        mock_controller.status_callback = None

                        main_task = asyncio.create_task(main(asyncio.get_event_loop()))

                        agent_ready_event = AgentStateChangedObservation(
                            agent_state=AgentState.AWAITING_USER_INPUT,
                            content='Agent is ready for user input',
                        )
                        mock_runtime.event_stream.add_event(
                            agent_ready_event, EventSource.AGENT
                        )

                        await asyncio.sleep(0.1)

                        try:
                            await asyncio.wait_for(main_task, timeout=0.5)
                        except asyncio.TimeoutError:
                            main_task.cancel()
                            try:
                                await main_task
                            except asyncio.CancelledError:
                                pass

                        # Verify that the exit command sent a STOPPED state change event
                        state_change_events = [
                            event
                            for event, source in mock_runtime.event_stream.events
                            if isinstance(event, ChangeAgentStateAction)
                            and event.agent_state == AgentState.STOPPED
                            and source == EventSource.ENVIRONMENT
                        ]
                        assert len(state_change_events) == 1

                        # Verify shutdown was called
                        mock_shutdown.assert_called_once()


@pytest.mark.asyncio
async def test_init_command(
    mock_runtime, mock_controller, mock_config, mock_agent, mock_memory, mock_read_task
):
    buffer = StringIO()

    with patch('openhands.core.cli.manage_openhands_file', return_value=True):
        with patch(
            'openhands.core.cli.check_folder_security_agreement', return_value=True
        ):
            with patch('openhands.core.cli.read_prompt_input') as mock_prompt:
                # First prompt call returns /init, second call returns /exit
                mock_prompt.side_effect = ['/init', '/exit']

                with patch('openhands.core.cli.init_repository') as mock_init_repo:
                    with create_app_session(
                        input=create_pipe_input(), output=create_output(stdout=buffer)
                    ):
                        mock_controller.status_callback = None

                        main_task = asyncio.create_task(main(asyncio.get_event_loop()))

                        agent_ready_event = AgentStateChangedObservation(
                            agent_state=AgentState.AWAITING_USER_INPUT,
                            content='Agent is ready for user input',
                        )
                        mock_runtime.event_stream.add_event(
                            agent_ready_event, EventSource.AGENT
                        )

                        await asyncio.sleep(0.1)

                        try:
                            await asyncio.wait_for(main_task, timeout=0.5)
                        except asyncio.TimeoutError:
                            main_task.cancel()
                            try:
                                await main_task
                            except asyncio.CancelledError:
                                pass

                        # Verify init_repository was called with the correct directory
                        mock_init_repo.assert_called_once_with('/test')

                        # Verify that a MessageAction was sent with the repository creation prompt
                        message_events = [
                            event
                            for event, source in mock_runtime.event_stream.events
                            if isinstance(event, MessageAction)
                            and 'Please explore this repository' in event.content
                            and source == EventSource.USER
                        ]
                        assert len(message_events) == 1


@pytest.mark.asyncio
async def test_init_command_non_local_runtime(
    mock_runtime, mock_controller, mock_config, mock_agent, mock_memory, mock_read_task
):
    buffer = StringIO()

    # Set runtime to non-local for this test
    mock_config.runtime = 'remote'

    with patch('openhands.core.cli.manage_openhands_file', return_value=True):
        with patch(
            'openhands.core.cli.check_folder_security_agreement', return_value=True
        ):
            with patch('openhands.core.cli.read_prompt_input') as mock_prompt:
                # First prompt call returns /init, second call returns /exit
                mock_prompt.side_effect = ['/init', '/exit']

                with patch('openhands.core.cli.init_repository') as mock_init_repo:
                    with create_app_session(
                        input=create_pipe_input(), output=create_output(stdout=buffer)
                    ):
                        mock_controller.status_callback = None

                        main_task = asyncio.create_task(main(asyncio.get_event_loop()))

                        # Send AgentStateChangedObservation to trigger prompt
                        agent_ready_event = AgentStateChangedObservation(
                            agent_state=AgentState.AWAITING_USER_INPUT,
                            content='Agent is ready for user input',
                        )
                        mock_runtime.event_stream.add_event(
                            agent_ready_event, EventSource.AGENT
                        )

                        await asyncio.sleep(0.1)

                        try:
                            await asyncio.wait_for(main_task, timeout=0.5)
                        except asyncio.TimeoutError:
                            main_task.cancel()
                            try:
                                await main_task
                            except asyncio.CancelledError:
                                pass

                        buffer.seek(0)
                        output = buffer.read()

                        # Verify error message was displayed
                        assert (
                            'Repository initialization through the CLI is only supported for local runtime'
                            in output
                        )

                        # Verify init_repository was not called
                        mock_init_repo.assert_not_called()

                        # Verify no MessageAction was sent for repository creation
                        message_events = [
                            event
                            for event, _ in mock_runtime.event_stream.events
                            if isinstance(event, MessageAction)
                            and 'Please explore this repository' in event.content
                        ]
                        assert len(message_events) == 0


@pytest.mark.asyncio
async def test_new_command_with_user_confirmation(
    mock_runtime, mock_controller, mock_config, mock_agent, mock_memory, mock_read_task
):
    buffer = StringIO()

    with patch('openhands.core.cli.manage_openhands_file', return_value=True), \
         patch('openhands.core.cli.check_folder_security_agreement', return_value=True), \
         patch('openhands.core.cli.read_prompt_input') as mock_prompt, \
         patch('openhands.core.cli.cli_confirm', return_value=0), \
         patch('openhands.core.cli.display_shutdown_message') as mock_shutdown, \
         patch('openhands.core.cli.clear'), \
         patch('openhands.core.cli.create_runtime', return_value=mock_runtime), \
         patch('openhands.core.cli.create_controller', return_value=(mock_controller, None)):

        # First prompt call returns /new, second returns /exit
        mock_prompt.side_effect = ['/new', '/exit']

        with create_app_session(
            input=create_pipe_input(), output=create_output(stdout=buffer)
        ):
            mock_controller.status_callback = None

            main_task = asyncio.create_task(main(asyncio.get_event_loop()))

            # Simulate agent ready state twice (once for initial start, once after /new)
            agent_ready_event = AgentStateChangedObservation(
                agent_state=AgentState.AWAITING_USER_INPUT,
                content='Agent is ready for user input',
            )
            mock_runtime.event_stream.add_event(agent_ready_event, EventSource.AGENT)
            # Add a small delay to allow the first loop iteration to process /new
            await asyncio.sleep(0.1)
            mock_runtime.event_stream.add_event(agent_ready_event, EventSource.AGENT)

            # Let the main loop run (should process /new then /exit)
            await asyncio.sleep(0.2)

            try:
                await asyncio.wait_for(main_task, timeout=0.5)
            except asyncio.TimeoutError:
                main_task.cancel()
                try:
                    await main_task
                except asyncio.CancelledError:
                    pass

            # Verify that two STOPPED state change events were sent (one for /new, one for /exit)
            state_change_events = [
                event
                for event, source in mock_runtime.event_stream.events
                if isinstance(event, ChangeAgentStateAction)
                and event.agent_state == AgentState.STOPPED
                and source == EventSource.ENVIRONMENT
            ]
            assert len(state_change_events) == 2, f"Expected 2 STOPPED events, got {len(state_change_events)}"

            # Verify shutdown message was called twice
            assert mock_shutdown.call_count == 2, f"Expected shutdown message twice, called {mock_shutdown.call_count} times"

@pytest.mark.asyncio
async def test_new_command_with_user_reject(
    mock_runtime, mock_controller, mock_config, mock_agent, mock_memory, mock_read_task
):
    buffer = StringIO()

    with patch('openhands.core.cli.manage_openhands_file', return_value=True), \
         patch('openhands.core.cli.check_folder_security_agreement', return_value=True), \
         patch('openhands.core.cli.read_prompt_input') as mock_prompt, \
         patch('openhands.core.cli.cli_confirm', return_value=1), \
         patch('openhands.core.cli.clear'), \
         patch('openhands.core.cli.create_runtime', return_value=mock_runtime), \
         patch('openhands.core.cli.create_controller', return_value=(mock_controller, None)):

        mock_prompt.side_effect = ['/new']

        with create_app_session(
            input=create_pipe_input(), output=create_output(stdout=buffer)
        ):
            mock_controller.status_callback = None

            main_task = asyncio.create_task(main(asyncio.get_event_loop()))

            agent_ready_event = AgentStateChangedObservation(
                agent_state=AgentState.AWAITING_USER_INPUT,
                content='Agent is ready for user input',
            )
            mock_runtime.event_stream.add_event(agent_ready_event, EventSource.AGENT)
            # Add a small delay to allow the first loop iteration to process /new
     
            # Let the main loop run
            await asyncio.sleep(0.2)

            try:
                await asyncio.wait_for(main_task, timeout=0.5)
            except asyncio.TimeoutError:
                main_task.cancel()
                try:
                    await main_task
                except asyncio.CancelledError:
                    pass

            # Verify that no STOPPED state change events were sent
            state_change_events = [
                event
                for event, source in mock_runtime.event_stream.events
                if isinstance(event, ChangeAgentStateAction)
                and event.agent_state == AgentState.STOPPED
                and source == EventSource.ENVIRONMENT
            ]
            assert len(state_change_events) == 0, f"Expected 0 STOPPED events, got {len(state_change_events)}"


@pytest.mark.asyncio
async def test_settings_command_display_basic_settings(
    mock_runtime, mock_controller, mock_config, mock_agent, mock_memory, mock_read_task
):
    buffer = StringIO()

    with patch('openhands.core.cli.manage_openhands_file', return_value=True), \
         patch('openhands.core.cli.check_folder_security_agreement', return_value=True), \
         patch('openhands.core.cli.read_prompt_input') as mock_prompt, \
         patch('openhands.core.cli.display_shutdown_message'), \
         patch('openhands.core.cli.cli_confirm', return_value=3) as mock_cli_confirm:
        
        # First prompt call returns /settings, second returns /exit
        mock_prompt.side_effect = ['/settings', '/exit']

        with create_app_session(
            input=create_pipe_input(), output=create_output(stdout=buffer)
        ):
            mock_controller.status_callback = None

            main_task = asyncio.create_task(main(asyncio.get_event_loop()))

            agent_ready_event = AgentStateChangedObservation(
                agent_state=AgentState.AWAITING_USER_INPUT,
                content='Agent is ready for user input',
            )
            mock_runtime.event_stream.add_event(
                agent_ready_event, EventSource.AGENT
            )

            await asyncio.sleep(0.1)

            try:
                await asyncio.wait_for(main_task, timeout=0.5)
            except asyncio.TimeoutError:
                main_task.cancel()
                try:
                    await main_task
                except asyncio.CancelledError:
                    pass

            buffer.seek(0)
            output = buffer.read()

            # Verify display_settings content
            assert 'Settings' in output
            assert 'LLM Provider' in output
            assert 'LLM Model' in output
            assert 'API Key' in output

            # Verify setting modification options
            mock_cli_confirm.assert_any_call('Which settings would you like to modify?', ['Basic', 'Advanced', 'Go back'])


@pytest.mark.asyncio
async def test_settings_command_display_advanced_settings(
    mock_runtime, mock_controller, mock_config, mock_agent, mock_memory, mock_read_task
):
    buffer = StringIO()

    with patch('openhands.core.cli.manage_openhands_file', return_value=True), \
         patch('openhands.core.cli.check_folder_security_agreement', return_value=True), \
         patch('openhands.core.cli.read_prompt_input') as mock_prompt, \
         patch('openhands.core.cli.display_shutdown_message'), \
         patch('openhands.core.config.app_config.AppConfig.get_llm_config', return_value=LLMConfig(base_url='test-base-url')), \
         patch('openhands.core.cli.cli_confirm', return_value=0) as mock_cli_confirm:

        # First prompt call returns /settings, second returns /exit
        mock_prompt.side_effect = ['/settings', '/exit']

        with create_app_session(
            input=create_pipe_input(), output=create_output(stdout=buffer)
        ):
            mock_controller.status_callback = None

            main_task = asyncio.create_task(main(asyncio.get_event_loop()))

            agent_ready_event = AgentStateChangedObservation(
                agent_state=AgentState.AWAITING_USER_INPUT,
                content='Agent is ready for user input',
            )
            mock_runtime.event_stream.add_event(
                agent_ready_event, EventSource.AGENT
            )

            await asyncio.sleep(0.1)

            try:
                await asyncio.wait_for(main_task, timeout=0.5)
            except asyncio.TimeoutError:
                main_task.cancel()
                try:
                    await main_task
                except asyncio.CancelledError:
                    pass

            buffer.seek(0)
            output = buffer.read()

            # Verify display_settings content
            assert 'Settings' in output
            assert 'Custom Model' in output
            assert 'Base URL' in output
            assert 'API Key' in output
            assert 'Agent' in output
            assert 'Confirmation Mode' in output
            assert 'Memory Condensation' in output

            # Verify setting modification options
            mock_cli_confirm.assert_any_call('Which settings would you like to modify?', ['Basic', 'Advanced', 'Go back'])


@pytest.mark.asyncio
async def test_settings_command_basic_llm_settings(
    mock_runtime, mock_controller, mock_config, mock_agent, mock_memory, mock_read_task
):
    buffer = StringIO()

    with patch('openhands.core.cli.manage_openhands_file', return_value=True), \
         patch('openhands.core.cli.check_folder_security_agreement', return_value=True), \
         patch('openhands.core.cli.read_prompt_input') as mock_prompt, \
         patch('openhands.core.cli.display_shutdown_message'), \
         patch('openhands.core.cli.display_settings', return_value=0), \
         patch('openhands.storage.settings.file_settings_store.FileSettingsStore.store') as mock_store, \
         patch('prompt_toolkit.PromptSession.prompt_async') as mock_prompt_async, \
         patch('openhands.core.cli.cli_confirm', return_value=0) as mock_cli_confirm:
        
        # First prompt call returns /settings, second returns /exit
        mock_prompt.side_effect = ['/settings', '/exit']

        mock_prompt_async.side_effect = ['openai', 'gpt-4o', 'sk-1234567890']

        with create_app_session(
            input=create_pipe_input(), output=create_output(stdout=buffer)
        ):
            mock_controller.status_callback = None

            main_task = asyncio.create_task(main(asyncio.get_event_loop()))

            agent_ready_event = AgentStateChangedObservation(
                agent_state=AgentState.AWAITING_USER_INPUT,
                content='Agent is ready for user input',
            )
            mock_runtime.event_stream.add_event(
                agent_ready_event, EventSource.AGENT
            )

            await asyncio.sleep(0.1)

            try:
                await asyncio.wait_for(main_task, timeout=0.5)
            except asyncio.TimeoutError:
                main_task.cancel()
                try:
                    await main_task
                except asyncio.CancelledError:
                    pass

            buffer.seek(0)
            output = buffer.read()

            # Verify prompts for basic llm settings
            mock_prompt_async.assert_any_call('(Step 1/3) Select LLM Provider (use Tab for completion): ', completer=ANY)
            mock_prompt_async.assert_any_call('(Step 2/3) Select LLM Model (use Tab for completion): ', completer=ANY)
            mock_prompt_async.assert_any_call('(Step 3/3) Enter API Key: ')

            # Verify save settings confirmation
            mock_cli_confirm.assert_any_call('\nSave new settings? Current session will be terminated!', ['Yes, proceed', 'No, dismiss'])


@pytest.mark.asyncio
async def test_settings_command_advanced_llm_settings(
    mock_runtime, mock_controller, mock_config, mock_agent, mock_memory, mock_read_task
):
    buffer = StringIO()

    with patch('openhands.core.cli.manage_openhands_file', return_value=True), \
         patch('openhands.core.cli.check_folder_security_agreement', return_value=True), \
         patch('openhands.core.cli.read_prompt_input') as mock_prompt, \
         patch('openhands.core.cli.display_shutdown_message'), \
         patch('openhands.core.cli.display_settings', return_value=1), \
         patch('openhands.storage.settings.file_settings_store.FileSettingsStore.store') as mock_store, \
         patch('prompt_toolkit.PromptSession.prompt_async') as mock_prompt_async, \
         patch('openhands.core.cli.cli_confirm', return_value=0) as mock_cli_confirm:
        
        # First prompt call returns /settings, second returns /exit
        mock_prompt.side_effect = ['/settings', '/exit']

        mock_prompt_async.side_effect = ['litellm/dummy_model', 'http://dummy_url', 'sk-01234567890', 'CodeActAgent']

        with create_app_session(
            input=create_pipe_input(), output=create_output(stdout=buffer)
        ):
            mock_controller.status_callback = None

            main_task = asyncio.create_task(main(asyncio.get_event_loop()))

            agent_ready_event = AgentStateChangedObservation(
                agent_state=AgentState.AWAITING_USER_INPUT,
                content='Agent is ready for user input',
            )
            mock_runtime.event_stream.add_event(
                agent_ready_event, EventSource.AGENT
            )

            await asyncio.sleep(0.1)

            try:
                await asyncio.wait_for(main_task, timeout=0.5)
            except asyncio.TimeoutError:
                main_task.cancel()
                try:
                    await main_task
                except asyncio.CancelledError:
                    pass

            buffer.seek(0)
            output = buffer.read()

            # Verify prompts for advanced llm settings
            mock_prompt_async.assert_any_call('(Step 1/6) Custom Model: ')
            mock_prompt_async.assert_any_call('(Step 2/6) Base URL: ')
            mock_prompt_async.assert_any_call('(Step 3/6) API Key: ')
            mock_prompt_async.assert_any_call('(Step 4/6) Agent (use Tab for completion): ', completer=ANY)
            mock_cli_confirm.assert_any_call(question='(Step 5/6) Confirmation Mode:', choices=['Enable', 'Disable'])
            mock_cli_confirm.assert_any_call(question='(Step 6/6) Memory Condensation:', choices=['Enable', 'Disable'])

            # Verify save settings confirmation
            mock_cli_confirm.assert_any_call('\nSave new settings? Current session will be terminated!', ['Yes, proceed', 'No, dismiss'])
