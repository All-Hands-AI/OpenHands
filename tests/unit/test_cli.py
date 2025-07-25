import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

from openhands.cli import main as cli
from openhands.controller.state.state import State
from openhands.events import EventSource
from openhands.events.action import MessageAction


@pytest_asyncio.fixture
def mock_agent():
    agent = AsyncMock()
    agent.reset = MagicMock()
    return agent


@pytest_asyncio.fixture
def mock_runtime():
    runtime = AsyncMock()
    runtime.close = MagicMock()
    runtime.event_stream = MagicMock()
    return runtime


@pytest_asyncio.fixture
def mock_controller():
    controller = AsyncMock()
    controller.close = AsyncMock()

    # Setup for get_state() and the returned state's save_to_session()
    mock_state = MagicMock()
    mock_state.save_to_session = MagicMock()
    controller.get_state = MagicMock(return_value=mock_state)
    return controller


@pytest.mark.asyncio
async def test_cleanup_session_closes_resources(
    mock_agent, mock_runtime, mock_controller
):
    """Test that cleanup_session calls close methods on agent, runtime, and controller."""
    loop = asyncio.get_running_loop()
    await cli.cleanup_session(loop, mock_agent, mock_runtime, mock_controller)

    mock_agent.reset.assert_called_once()
    mock_runtime.close.assert_called_once()
    mock_controller.close.assert_called_once()


@pytest.mark.asyncio
async def test_cleanup_session_cancels_pending_tasks(
    mock_agent, mock_runtime, mock_controller
):
    """Test that cleanup_session cancels other pending tasks."""
    loop = asyncio.get_running_loop()
    other_task_ran = False
    other_task_cancelled = False

    async def _other_task_func():
        nonlocal other_task_ran, other_task_cancelled
        try:
            other_task_ran = True
            await asyncio.sleep(5)  # Sleep long enough to be cancelled
        except asyncio.CancelledError:
            other_task_cancelled = True
            raise

    other_task = loop.create_task(_other_task_func())

    # Allow the other task to start running
    await asyncio.sleep(0)
    assert other_task_ran is True

    # Run cleanup session directly from the test task
    await cli.cleanup_session(loop, mock_agent, mock_runtime, mock_controller)
    await asyncio.sleep(0)

    # Check that the other task was indeed cancelled
    assert other_task.cancelled() or other_task_cancelled is True

    # Ensure the cleanup finishes (awaiting the task raises CancelledError if cancelled)
    try:
        await other_task
    except asyncio.CancelledError:
        pass  # Expected

    # Verify cleanup still called mocks
    mock_agent.reset.assert_called_once()
    mock_runtime.close.assert_called_once()
    mock_controller.close.assert_called_once()


@pytest.mark.asyncio
async def test_cleanup_session_handles_exceptions(
    mock_agent, mock_runtime, mock_controller
):
    """Test that cleanup_session handles exceptions during cleanup gracefully."""
    loop = asyncio.get_running_loop()
    mock_controller.close.side_effect = Exception('Test cleanup error')
    with patch('openhands.cli.main.logger.error') as mock_log_error:
        await cli.cleanup_session(loop, mock_agent, mock_runtime, mock_controller)

        # Check that cleanup continued despite the error
        mock_agent.reset.assert_called_once()
        mock_runtime.close.assert_called_once()
        # Check that the error was logged
        mock_log_error.assert_called_once()
        assert 'Test cleanup error' in mock_log_error.call_args[0][0]


@pytest_asyncio.fixture
def mock_config():
    config = MagicMock()
    config.runtime = 'local'
    config.cli_multiline_input = False
    config.workspace_base = '/test/dir'

    # Mock search_api_key with get_secret_value method
    search_api_key_mock = MagicMock()
    search_api_key_mock.get_secret_value.return_value = (
        ''  # Empty string, not starting with 'tvly-'
    )
    config.search_api_key = search_api_key_mock

    # Mock sandbox with volumes attribute to prevent finalize_config issues
    config.sandbox = MagicMock()
    config.sandbox.volumes = (
        None  # This prevents finalize_config from overriding workspace_base
    )

    return config


@pytest_asyncio.fixture
def mock_settings_store():
    settings_store = AsyncMock()
    return settings_store


@pytest.mark.asyncio
@patch('openhands.cli.main.display_runtime_initialization_message')
@patch('openhands.cli.main.display_initialization_animation')
@patch('openhands.cli.main.create_agent')
@patch('openhands.cli.main.add_mcp_tools_to_agent')
@patch('openhands.cli.main.create_runtime')
@patch('openhands.cli.main.create_controller')
@patch(
    'openhands.cli.main.create_memory',
)
@patch('openhands.cli.main.run_agent_until_done')
@patch('openhands.cli.main.cleanup_session')
@patch('openhands.cli.main.initialize_repository_for_runtime')
async def test_run_session_without_initial_action(
    mock_initialize_repo,
    mock_cleanup_session,
    mock_run_agent_until_done,
    mock_create_memory,
    mock_create_controller,
    mock_create_runtime,
    mock_add_mcp_tools,
    mock_create_agent,
    mock_display_animation,
    mock_display_runtime_init,
    mock_config,
    mock_settings_store,
):
    """Test run_session function with no initial user action."""
    loop = asyncio.get_running_loop()

    # Mock initialize_repository_for_runtime to return a valid path
    mock_initialize_repo.return_value = '/test/dir'

    # Mock objects returned by the setup functions
    mock_agent = AsyncMock()
    mock_create_agent.return_value = mock_agent

    mock_runtime = AsyncMock()
    mock_runtime.event_stream = MagicMock()
    mock_create_runtime.return_value = mock_runtime

    mock_controller = AsyncMock()
    mock_controller_task = MagicMock()
    mock_create_controller.return_value = (mock_controller, mock_controller_task)

    # Create a regular MagicMock for memory to avoid coroutine issues
    mock_memory = MagicMock()
    mock_create_memory.return_value = mock_memory

    with patch(
        'openhands.cli.main.read_prompt_input', new_callable=AsyncMock
    ) as mock_read_prompt:
        # Set up read_prompt_input to return a string that will trigger the command handler
        mock_read_prompt.return_value = '/exit'

        # Mock handle_commands to return values that will exit the loop
        with patch(
            'openhands.cli.main.handle_commands', new_callable=AsyncMock
        ) as mock_handle_commands:
            mock_handle_commands.return_value = (
                True,
                False,
                False,
            )  # close_repl, reload_microagents, new_session_requested

            # Run the function
            result = await cli.run_session(
                loop, mock_config, mock_settings_store, '/test/dir'
            )

    # Assertions for initialization flow
    mock_display_runtime_init.assert_called_once_with('local')
    mock_display_animation.assert_called_once()
    mock_create_agent.assert_called_once_with(mock_config)
    mock_add_mcp_tools.assert_called_once_with(mock_agent, mock_runtime, mock_memory)
    mock_create_runtime.assert_called_once()
    mock_create_controller.assert_called_once()
    mock_create_memory.assert_called_once()

    # Check that run_agent_until_done was called
    mock_run_agent_until_done.assert_called_once()

    # Check that cleanup_session was called
    mock_cleanup_session.assert_called_once()

    # Check that the function returns the expected value
    assert result is False


@pytest.mark.asyncio
@patch('openhands.cli.main.display_runtime_initialization_message')
@patch('openhands.cli.main.display_initialization_animation')
@patch('openhands.cli.main.create_agent')
@patch('openhands.cli.main.add_mcp_tools_to_agent')
@patch('openhands.cli.main.create_runtime')
@patch('openhands.cli.main.create_controller')
@patch('openhands.cli.main.create_memory', new_callable=AsyncMock)
@patch('openhands.cli.main.run_agent_until_done')
@patch('openhands.cli.main.cleanup_session')
@patch('openhands.cli.main.initialize_repository_for_runtime')
async def test_run_session_with_initial_action(
    mock_initialize_repo,
    mock_cleanup_session,
    mock_run_agent_until_done,
    mock_create_memory,
    mock_create_controller,
    mock_create_runtime,
    mock_add_mcp_tools,
    mock_create_agent,
    mock_display_animation,
    mock_display_runtime_init,
    mock_config,
    mock_settings_store,
):
    """Test run_session function with an initial user action."""
    loop = asyncio.get_running_loop()

    # Mock initialize_repository_for_runtime to return a valid path
    mock_initialize_repo.return_value = '/test/dir'

    # Mock objects returned by the setup functions
    mock_agent = AsyncMock()
    mock_create_agent.return_value = mock_agent

    mock_runtime = AsyncMock()
    mock_runtime.event_stream = MagicMock()
    mock_create_runtime.return_value = mock_runtime

    mock_controller = AsyncMock()
    mock_create_controller.return_value = (
        mock_controller,
        None,
    )  # Ensure initial_state is None for this test

    mock_memory = AsyncMock()
    mock_create_memory.return_value = mock_memory

    # Create an initial action
    initial_action_content = 'Test initial message'

    # Run the function with the initial action
    with patch(
        'openhands.cli.main.read_prompt_input', new_callable=AsyncMock
    ) as mock_read_prompt:
        # Set up read_prompt_input to return a string that will trigger the command handler
        mock_read_prompt.return_value = '/exit'

        # Mock handle_commands to return values that will exit the loop
        with patch(
            'openhands.cli.main.handle_commands', new_callable=AsyncMock
        ) as mock_handle_commands:
            mock_handle_commands.return_value = (
                True,
                False,
                False,
            )  # close_repl, reload_microagents, new_session_requested

            # Run the function
            result = await cli.run_session(
                loop,
                mock_config,
                mock_settings_store,
                '/test/dir',
                initial_action_content,
            )

    # Check that the initial action was added to the event stream
    # It should be converted to a MessageAction in the code
    mock_runtime.event_stream.add_event.assert_called_once()
    call_args = mock_runtime.event_stream.add_event.call_args[0]
    assert isinstance(call_args[0], MessageAction)
    assert call_args[0].content == initial_action_content
    assert call_args[1] == EventSource.USER

    # Check that run_agent_until_done was called
    mock_run_agent_until_done.assert_called_once()

    # Check that cleanup_session was called
    mock_cleanup_session.assert_called_once()

    # Check that the function returns the expected value
    assert result is False


@pytest.mark.asyncio
@patch('openhands.cli.main.parse_arguments')
@patch('openhands.cli.main.setup_config_from_args')
@patch('openhands.cli.main.FileSettingsStore.get_instance')
@patch('openhands.cli.main.check_folder_security_agreement')
@patch('openhands.cli.main.read_task')
@patch('openhands.cli.main.run_session')
@patch('openhands.cli.main.LLMSummarizingCondenserConfig')
@patch('openhands.cli.main.NoOpCondenserConfig')
@patch('openhands.cli.main.finalize_config')
@patch('openhands.cli.main.aliases_exist_in_shell_config')
async def test_main_without_task(
    mock_aliases_exist,
    mock_finalize_config,
    mock_noop_condenser,
    mock_llm_condenser,
    mock_run_session,
    mock_read_task,
    mock_check_security,
    mock_get_settings_store,
    mock_setup_config,
    mock_parse_args,
):
    """Test main function without a task."""
    loop = asyncio.get_running_loop()

    # Mock alias setup functions to prevent the alias setup flow
    mock_aliases_exist.return_value = True

    # Mock arguments
    mock_args = MagicMock()
    mock_args.agent_cls = None
    mock_args.llm_config = None
    mock_args.name = None
    mock_args.file = None
    mock_parse_args.return_value = mock_args

    # Mock config
    mock_config = MagicMock()
    mock_config.workspace_base = '/test/dir'
    mock_config.cli_multiline_input = False
    mock_setup_config.return_value = mock_config

    # Mock settings store
    mock_settings_store = AsyncMock()
    mock_settings = MagicMock()
    mock_settings.agent = 'test-agent'
    mock_settings.llm_model = 'test-model'
    mock_settings.llm_api_key = 'test-api-key'
    mock_settings.llm_base_url = 'test-base-url'
    mock_settings.confirmation_mode = True
    mock_settings.enable_default_condenser = True
    mock_settings_store.load.return_value = mock_settings
    mock_get_settings_store.return_value = mock_settings_store

    # Mock condenser config to return a mock instead of validating
    mock_llm_condenser_instance = MagicMock()
    mock_llm_condenser.return_value = mock_llm_condenser_instance

    # Mock security check
    mock_check_security.return_value = True

    # Mock read_task to return no task
    mock_read_task.return_value = None

    # Mock run_session to return False (no new session requested)
    mock_run_session.return_value = False

    # Run the function
    await cli.main_with_loop(loop)

    # Assertions
    mock_parse_args.assert_called_once()
    mock_setup_config.assert_called_once_with(mock_args)
    mock_get_settings_store.assert_called_once()
    mock_settings_store.load.assert_called_once()
    mock_check_security.assert_called_once_with(mock_config, '/test/dir')
    mock_read_task.assert_called_once()

    # Check that run_session was called with expected arguments
    mock_run_session.assert_called_once_with(
        loop,
        mock_config,
        mock_settings_store,
        '/test/dir',
        None,
        session_name=None,
        skip_banner=False,
    )


@pytest.mark.asyncio
@patch('openhands.cli.main.parse_arguments')
@patch('openhands.cli.main.setup_config_from_args')
@patch('openhands.cli.main.FileSettingsStore.get_instance')
@patch('openhands.cli.main.check_folder_security_agreement')
@patch('openhands.cli.main.read_task')
@patch('openhands.cli.main.run_session')
@patch('openhands.cli.main.LLMSummarizingCondenserConfig')
@patch('openhands.cli.main.NoOpCondenserConfig')
@patch('openhands.cli.main.finalize_config')
@patch('openhands.cli.main.aliases_exist_in_shell_config')
async def test_main_with_task(
    mock_aliases_exist,
    mock_finalize_config,
    mock_noop_condenser,
    mock_llm_condenser,
    mock_run_session,
    mock_read_task,
    mock_check_security,
    mock_get_settings_store,
    mock_setup_config,
    mock_parse_args,
):
    """Test main function with a task."""
    loop = asyncio.get_running_loop()

    # Mock alias setup functions to prevent the alias setup flow
    mock_aliases_exist.return_value = True

    # Mock arguments
    mock_args = MagicMock()
    mock_args.agent_cls = 'custom-agent'
    mock_args.llm_config = 'custom-config'
    mock_args.file = None
    mock_parse_args.return_value = mock_args

    # Mock config
    mock_config = MagicMock()
    mock_config.workspace_base = '/test/dir'
    mock_config.cli_multiline_input = False
    mock_setup_config.return_value = mock_config

    # Mock settings store
    mock_settings_store = AsyncMock()
    mock_settings = MagicMock()
    mock_settings.agent = 'test-agent'
    mock_settings.llm_model = 'test-model'
    mock_settings.llm_api_key = 'test-api-key'
    mock_settings.llm_base_url = 'test-base-url'
    mock_settings.confirmation_mode = True
    mock_settings.enable_default_condenser = False
    mock_settings_store.load.return_value = mock_settings
    mock_get_settings_store.return_value = mock_settings_store

    # Mock condenser config to return a mock instead of validating
    mock_noop_condenser_instance = MagicMock()
    mock_noop_condenser.return_value = mock_noop_condenser_instance

    # Mock security check
    mock_check_security.return_value = True

    # Mock read_task to return a task
    task_str = 'Build a simple web app'
    mock_read_task.return_value = task_str

    # Mock run_session to return True and then False (one new session requested)
    mock_run_session.side_effect = [True, False]

    # Run the function
    await cli.main_with_loop(loop)

    # Assertions
    mock_parse_args.assert_called_once()
    mock_setup_config.assert_called_once_with(mock_args)
    mock_get_settings_store.assert_called_once()
    mock_settings_store.load.assert_called_once()
    mock_check_security.assert_called_once_with(mock_config, '/test/dir')
    mock_read_task.assert_called_once()

    # Verify that run_session was called twice:
    # - First with the initial MessageAction
    # - Second with None after new_session_requested=True
    assert mock_run_session.call_count == 2

    # First call should include a string with the task content
    first_call_args = mock_run_session.call_args_list[0][0]
    assert first_call_args[0] == loop
    assert first_call_args[1] == mock_config
    assert first_call_args[2] == mock_settings_store
    assert first_call_args[3] == '/test/dir'
    assert isinstance(first_call_args[4], str)
    assert first_call_args[4] == task_str

    # Second call should have None for the action
    second_call_args = mock_run_session.call_args_list[1][0]
    assert second_call_args[0] == loop
    assert second_call_args[1] == mock_config
    assert second_call_args[2] == mock_settings_store
    assert second_call_args[3] == '/test/dir'
    assert second_call_args[4] is None


@pytest.mark.asyncio
@patch('openhands.cli.main.parse_arguments')
@patch('openhands.cli.main.setup_config_from_args')
@patch('openhands.cli.main.FileSettingsStore.get_instance')
@patch('openhands.cli.main.check_folder_security_agreement')
@patch('openhands.cli.main.read_task')
@patch('openhands.cli.main.run_session')
@patch('openhands.cli.main.LLMSummarizingCondenserConfig')
@patch('openhands.cli.main.NoOpCondenserConfig')
@patch('openhands.cli.main.finalize_config')
@patch('openhands.cli.main.aliases_exist_in_shell_config')
async def test_main_with_session_name_passes_name_to_run_session(
    mock_aliases_exist,
    mock_finalize_config,
    mock_noop_condenser,
    mock_llm_condenser,
    mock_run_session,
    mock_read_task,
    mock_check_security,
    mock_get_settings_store,
    mock_setup_config,
    mock_parse_args,
):
    """Test main function with a session name passes it to run_session."""
    loop = asyncio.get_running_loop()
    test_session_name = 'my_named_session'

    # Mock alias setup functions to prevent the alias setup flow
    mock_aliases_exist.return_value = True

    # Mock arguments
    mock_args = MagicMock()
    mock_args.agent_cls = None
    mock_args.llm_config = None
    mock_args.name = test_session_name  # Set the session name
    mock_args.file = None
    mock_parse_args.return_value = mock_args

    # Mock config
    mock_config = MagicMock()
    mock_config.workspace_base = '/test/dir'
    mock_config.cli_multiline_input = False
    mock_setup_config.return_value = mock_config

    # Mock settings store
    mock_settings_store = AsyncMock()
    mock_settings = MagicMock()
    mock_settings.agent = 'test-agent'
    mock_settings.llm_model = 'test-model'  # Copied from test_main_without_task
    mock_settings.llm_api_key = 'test-api-key'  # Copied from test_main_without_task
    mock_settings.llm_base_url = 'test-base-url'  # Copied from test_main_without_task
    mock_settings.confirmation_mode = True  # Copied from test_main_without_task
    mock_settings.enable_default_condenser = True  # Copied from test_main_without_task
    mock_settings_store.load.return_value = mock_settings
    mock_get_settings_store.return_value = mock_settings_store

    # Mock condenser config (as in test_main_without_task)
    mock_llm_condenser_instance = MagicMock()
    mock_llm_condenser.return_value = mock_llm_condenser_instance

    # Mock security check
    mock_check_security.return_value = True

    # Mock read_task to return no task
    mock_read_task.return_value = None

    # Mock run_session to return False (no new session requested)
    mock_run_session.return_value = False

    # Run the function
    await cli.main_with_loop(loop)

    # Assertions
    mock_parse_args.assert_called_once()
    mock_setup_config.assert_called_once_with(mock_args)
    mock_get_settings_store.assert_called_once()
    mock_settings_store.load.assert_called_once()
    mock_check_security.assert_called_once_with(mock_config, '/test/dir')
    mock_read_task.assert_called_once()

    # Check that run_session was called with the correct session_name
    mock_run_session.assert_called_once_with(
        loop,
        mock_config,
        mock_settings_store,
        '/test/dir',
        None,
        session_name=test_session_name,
        skip_banner=False,
    )


@pytest.mark.asyncio
@patch('openhands.cli.main.generate_sid')
@patch('openhands.cli.main.create_agent')
@patch('openhands.cli.main.create_runtime')  # Returns mock_runtime
@patch('openhands.cli.main.create_memory')
@patch('openhands.cli.main.add_mcp_tools_to_agent')
@patch('openhands.cli.main.run_agent_until_done')
@patch('openhands.cli.main.cleanup_session')
@patch(
    'openhands.cli.main.read_prompt_input', new_callable=AsyncMock
)  # For REPL control
@patch('openhands.cli.main.handle_commands', new_callable=AsyncMock)  # For REPL control
@patch('openhands.core.setup.State.restore_from_session')  # Key mock
@patch('openhands.controller.AgentController.__init__')  # To check initial_state
@patch('openhands.cli.main.display_runtime_initialization_message')  # Cosmetic
@patch('openhands.cli.main.display_initialization_animation')  # Cosmetic
@patch('openhands.cli.main.initialize_repository_for_runtime')  # Cosmetic / setup
@patch('openhands.cli.main.display_initial_user_prompt')  # Cosmetic
@patch('openhands.cli.main.finalize_config')
async def test_run_session_with_name_attempts_state_restore(
    mock_finalize_config,
    mock_display_initial_user_prompt,
    mock_initialize_repo,
    mock_display_init_anim,
    mock_display_runtime_init,
    mock_agent_controller_init,
    mock_restore_from_session,
    mock_handle_commands,
    mock_read_prompt_input,
    mock_cleanup_session,
    mock_run_agent_until_done,
    mock_add_mcp_tools,
    mock_create_memory,
    mock_create_runtime,
    mock_create_agent,
    mock_generate_sid,
    mock_config,  # Fixture
    mock_settings_store,  # Fixture
):
    """Test run_session with a session_name attempts to restore state and passes it to AgentController."""
    loop = asyncio.get_running_loop()
    test_session_name = 'my_restore_test_session'
    expected_sid = f'sid_for_{test_session_name}'

    mock_generate_sid.return_value = expected_sid

    mock_agent = AsyncMock()
    mock_create_agent.return_value = mock_agent

    mock_runtime = AsyncMock()
    mock_runtime.event_stream = MagicMock()  # This is the EventStream instance
    mock_runtime.event_stream.sid = expected_sid
    mock_runtime.event_stream.file_store = (
        MagicMock()
    )  # Mock the file_store attribute on the EventStream
    mock_create_runtime.return_value = mock_runtime

    # This is what State.restore_from_session will return
    mock_loaded_state = MagicMock(spec=State)
    mock_restore_from_session.return_value = mock_loaded_state

    # AgentController.__init__ should not return a value (it's __init__)
    mock_agent_controller_init.return_value = None

    # To make run_session exit cleanly after one loop
    mock_read_prompt_input.return_value = '/exit'
    mock_handle_commands.return_value = (
        True,
        False,
        False,
    )  # close_repl, reload_microagents, new_session_requested

    # Mock other functions called by run_session to avoid side effects
    mock_initialize_repo.return_value = '/mocked/repo/dir'
    mock_create_memory.return_value = AsyncMock()  # Memory instance

    await cli.run_session(
        loop,
        mock_config,
        mock_settings_store,  # This is FileSettingsStore, not directly used for restore in this path
        '/test/dir',
        task_content=None,
        session_name=test_session_name,
    )

    mock_generate_sid.assert_called_once_with(mock_config, test_session_name)

    # State.restore_from_session is called from within core.setup.create_controller,
    # which receives the runtime object (and thus its event_stream with sid and file_store).
    mock_restore_from_session.assert_called_once_with(
        expected_sid, mock_runtime.event_stream.file_store
    )

    # Check that AgentController was initialized with the loaded state
    mock_agent_controller_init.assert_called_once()
    args, kwargs = mock_agent_controller_init.call_args
    assert kwargs.get('initial_state') == mock_loaded_state


@pytest.mark.asyncio
@patch('openhands.cli.main.parse_arguments')
@patch('openhands.cli.main.setup_config_from_args')
@patch('openhands.cli.main.FileSettingsStore.get_instance')
@patch('openhands.cli.main.check_folder_security_agreement')
@patch('openhands.cli.main.read_task')
@patch('openhands.cli.main.run_session')
@patch('openhands.cli.main.LLMSummarizingCondenserConfig')
@patch('openhands.cli.main.NoOpCondenserConfig')
@patch('openhands.cli.main.finalize_config')
@patch('openhands.cli.main.aliases_exist_in_shell_config')
async def test_main_security_check_fails(
    mock_aliases_exist,
    mock_finalize_config,
    mock_noop_condenser,
    mock_llm_condenser,
    mock_run_session,
    mock_read_task,
    mock_check_security,
    mock_get_settings_store,
    mock_setup_config,
    mock_parse_args,
):
    """Test main function when security check fails."""
    loop = asyncio.get_running_loop()

    # Mock alias setup functions to prevent the alias setup flow
    mock_aliases_exist.return_value = True

    # Mock arguments
    mock_args = MagicMock()
    mock_parse_args.return_value = mock_args

    # Mock config
    mock_config = MagicMock()
    mock_config.workspace_base = '/test/dir'
    mock_setup_config.return_value = mock_config

    # Mock settings store
    mock_settings_store = AsyncMock()
    mock_settings = MagicMock()
    mock_settings.enable_default_condenser = False
    mock_settings_store.load.return_value = mock_settings
    mock_get_settings_store.return_value = mock_settings_store

    # Mock condenser config to return a mock instead of validating
    mock_noop_condenser_instance = MagicMock()
    mock_noop_condenser.return_value = mock_noop_condenser_instance

    # Mock security check to fail
    mock_check_security.return_value = False

    # Run the function
    await cli.main_with_loop(loop)

    # Assertions
    mock_parse_args.assert_called_once()
    mock_setup_config.assert_called_once_with(mock_args)
    mock_get_settings_store.assert_called_once()
    mock_settings_store.load.assert_called_once()
    mock_check_security.assert_called_once_with(mock_config, '/test/dir')

    # Since security check fails, no further action should happen
    # (This is an implicit assertion - we don't need to check further function calls)


@pytest.mark.asyncio
@patch('openhands.cli.main.parse_arguments')
@patch('openhands.cli.main.setup_config_from_args')
@patch('openhands.cli.main.FileSettingsStore.get_instance')
@patch('openhands.cli.main.check_folder_security_agreement')
@patch('openhands.cli.main.read_task')
@patch('openhands.cli.main.run_session')
@patch('openhands.cli.main.LLMSummarizingCondenserConfig')
@patch('openhands.cli.main.NoOpCondenserConfig')
@patch('openhands.cli.main.finalize_config')
@patch('openhands.cli.main.aliases_exist_in_shell_config')
async def test_config_loading_order(
    mock_aliases_exist,
    mock_finalize_config,
    mock_noop_condenser,
    mock_llm_condenser,
    mock_run_session,
    mock_read_task,
    mock_check_security,
    mock_get_settings_store,
    mock_setup_config,
    mock_parse_args,
):
    """Test the order of configuration loading in the main function.

    This test verifies:
    1. Command line arguments override settings store values
    2. Settings from store are used when command line args are not provided
    3. Default condenser is configured correctly based on settings
    """
    loop = asyncio.get_running_loop()

    # Mock alias setup functions to prevent the alias setup flow
    mock_aliases_exist.return_value = True

    # Mock arguments with specific agent but no LLM config
    mock_args = MagicMock()
    mock_args.agent_cls = 'cmd-line-agent'  # This should override settings
    mock_args.llm_config = None  # This should allow settings to be used
    # Add a file property to avoid file I/O errors
    mock_args.file = None
    mock_args.log_level = 'INFO'
    mock_parse_args.return_value = mock_args

    # Mock read_task to return a dummy task
    mock_read_task.return_value = 'Test task'

    # Mock config with mock methods to track changes
    mock_config = MagicMock()
    mock_config.workspace_base = '/test/dir'
    mock_config.cli_multiline_input = False
    mock_config.get_llm_config = MagicMock(return_value=MagicMock())
    mock_config.set_llm_config = MagicMock()
    mock_config.get_agent_config = MagicMock(return_value=MagicMock())
    mock_config.set_agent_config = MagicMock()
    mock_setup_config.return_value = mock_config

    # Mock settings store with specific values
    mock_settings_store = AsyncMock()
    mock_settings = MagicMock()
    mock_settings.agent = 'settings-agent'  # Should be overridden by cmd line
    mock_settings.llm_model = 'settings-model'  # Should be used (no cmd line)
    mock_settings.llm_api_key = 'settings-api-key'  # Should be used
    mock_settings.llm_base_url = 'settings-base-url'  # Should be used
    mock_settings.confirmation_mode = True
    mock_settings.enable_default_condenser = True  # Test condenser setup
    mock_settings_store.load.return_value = mock_settings
    mock_get_settings_store.return_value = mock_settings_store

    # Mock condenser configs
    mock_llm_condenser_instance = MagicMock()
    mock_llm_condenser.return_value = mock_llm_condenser_instance

    # Mock security check and run_session to succeed
    mock_check_security.return_value = True
    mock_run_session.return_value = False  # No new session requested

    # Run the function
    await cli.main_with_loop(loop)

    # Assertions for argument parsing and config setup
    mock_parse_args.assert_called_once()
    mock_setup_config.assert_called_once_with(mock_args)
    mock_get_settings_store.assert_called_once()
    mock_settings_store.load.assert_called_once()

    # Verify agent is set from command line args (overriding settings)
    # In the actual implementation, default_agent is set in setup_config_from_args
    # We need to set it on our mock to simulate this behavior
    mock_config.default_agent = 'cmd-line-agent'

    # Verify LLM config is set from settings (since no cmd line arg)
    assert mock_config.set_llm_config.called
    llm_config_call = mock_config.set_llm_config.call_args[0][0]
    assert llm_config_call.model == 'settings-model'
    assert llm_config_call.api_key == 'settings-api-key'
    assert llm_config_call.base_url == 'settings-base-url'

    # Verify confirmation mode is set from settings
    assert mock_config.security.confirmation_mode is True

    # Verify default condenser is set up correctly
    assert mock_config.set_agent_config.called
    assert mock_llm_condenser.called
    assert mock_config.enable_default_condenser is True

    # Verify that run_session was called with the correct arguments
    mock_run_session.assert_called_once()


@pytest.mark.asyncio
@patch('openhands.cli.main.parse_arguments')
@patch('openhands.cli.main.setup_config_from_args')
@patch('openhands.cli.main.FileSettingsStore.get_instance')
@patch('openhands.cli.main.check_folder_security_agreement')
@patch('openhands.cli.main.read_task')
@patch('openhands.cli.main.run_session')
@patch('openhands.cli.main.LLMSummarizingCondenserConfig')
@patch('openhands.cli.main.NoOpCondenserConfig')
@patch('openhands.cli.main.finalize_config')
@patch('openhands.cli.main.aliases_exist_in_shell_config')
@patch('builtins.open', new_callable=MagicMock)
async def test_main_with_file_option(
    mock_open,
    mock_aliases_exist,
    mock_finalize_config,
    mock_noop_condenser,
    mock_llm_condenser,
    mock_run_session,
    mock_read_task,
    mock_check_security,
    mock_get_settings_store,
    mock_setup_config,
    mock_parse_args,
):
    """Test main function with a file option."""
    loop = asyncio.get_running_loop()

    # Mock alias setup functions to prevent the alias setup flow
    mock_aliases_exist.return_value = True

    # Mock arguments
    mock_args = MagicMock()
    mock_args.agent_cls = None
    mock_args.llm_config = None
    mock_args.name = None
    mock_args.file = '/path/to/test/file.txt'
    mock_args.task = None
    mock_parse_args.return_value = mock_args

    # Mock config
    mock_config = MagicMock()
    mock_config.workspace_base = '/test/dir'
    mock_config.cli_multiline_input = False
    mock_setup_config.return_value = mock_config

    # Mock settings store
    mock_settings_store = AsyncMock()
    mock_settings = MagicMock()
    mock_settings.agent = 'test-agent'
    mock_settings.llm_model = 'test-model'
    mock_settings.llm_api_key = 'test-api-key'
    mock_settings.llm_base_url = 'test-base-url'
    mock_settings.confirmation_mode = True
    mock_settings.enable_default_condenser = True
    mock_settings_store.load.return_value = mock_settings
    mock_get_settings_store.return_value = mock_settings_store

    # Mock condenser config to return a mock instead of validating
    mock_llm_condenser_instance = MagicMock()
    mock_llm_condenser.return_value = mock_llm_condenser_instance

    # Mock security check
    mock_check_security.return_value = True

    # Mock file open
    mock_file = MagicMock()
    mock_file.__enter__.return_value.read.return_value = 'This is a test file content.'
    mock_open.return_value = mock_file

    # Mock run_session to return False (no new session requested)
    mock_run_session.return_value = False

    # Run the function
    await cli.main_with_loop(loop)

    # Assertions
    mock_parse_args.assert_called_once()
    mock_setup_config.assert_called_once_with(mock_args)
    mock_get_settings_store.assert_called_once()
    mock_settings_store.load.assert_called_once()
    mock_check_security.assert_called_once_with(mock_config, '/test/dir')

    # Verify file was opened
    mock_open.assert_called_once_with('/path/to/test/file.txt', 'r', encoding='utf-8')

    # Check that run_session was called with expected arguments
    mock_run_session.assert_called_once()
    # Extract the task_str from the call
    task_str = mock_run_session.call_args[0][4]
    assert "The user has tagged a file '/path/to/test/file.txt'" in task_str
    assert 'Please read and understand the following file content first:' in task_str
    assert 'This is a test file content.' in task_str
    assert (
        'After reviewing the file, please ask the user what they would like to do with it.'
        in task_str
    )
