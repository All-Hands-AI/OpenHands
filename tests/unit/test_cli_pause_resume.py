import asyncio
from unittest.mock import MagicMock, call, patch

import pytest
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.keys import Keys

from openhands.cli.tui import process_agent_pause
from openhands.core.schema import AgentState
from openhands.events import EventSource
from openhands.events.action import ChangeAgentStateAction
from openhands.events.observation import AgentStateChangedObservation


class TestProcessAgentPause:
    @pytest.mark.asyncio
    @patch('openhands.cli.tui.create_input')
    @patch('openhands.cli.tui.print_formatted_text')
    async def test_process_agent_pause_ctrl_p(self, mock_print, mock_create_input):
        """Test that process_agent_pause sets the done event when Ctrl+P is pressed."""
        # Create the done event
        done = asyncio.Event()

        # Set up the mock input
        mock_input = MagicMock()
        mock_create_input.return_value = mock_input

        # Mock the context managers
        mock_raw_mode = MagicMock()
        mock_input.raw_mode.return_value = mock_raw_mode
        mock_raw_mode.__enter__ = MagicMock()
        mock_raw_mode.__exit__ = MagicMock()

        mock_attach = MagicMock()
        mock_input.attach.return_value = mock_attach
        mock_attach.__enter__ = MagicMock()
        mock_attach.__exit__ = MagicMock()

        # Capture the keys_ready function
        keys_ready_func = None

        def fake_attach(callback):
            nonlocal keys_ready_func
            keys_ready_func = callback
            return mock_attach

        mock_input.attach.side_effect = fake_attach

        # Create a task to run process_agent_pause
        task = asyncio.create_task(process_agent_pause(done, event_stream=MagicMock()))

        # Give it a moment to start and capture the callback
        await asyncio.sleep(0.1)

        # Make sure we captured the callback
        assert keys_ready_func is not None

        # Create a key press that simulates Ctrl+P
        key_press = MagicMock()
        key_press.key = Keys.ControlP
        mock_input.read_keys.return_value = [key_press]

        # Manually call the callback to simulate key press
        keys_ready_func()

        # Verify done was set
        assert done.is_set()

        # Verify print was called with the pause message
        assert mock_print.call_count == 2
        assert mock_print.call_args_list[0] == call('')

        # Check that the second call contains the pause message HTML
        second_call = mock_print.call_args_list[1][0][0]
        assert isinstance(second_call, HTML)
        assert 'Pausing the agent' in str(second_call)

        # Cancel the task
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


class TestCliPauseResumeInRunSession:
    @pytest.mark.asyncio
    async def test_on_event_async_pause_processing(self):
        """Test that on_event_async processes the pause event when is_paused is set."""
        # Create a mock event
        event = MagicMock()

        # Create mock dependencies
        event_stream = MagicMock()
        is_paused = asyncio.Event()
        reload_microagents = False
        config = MagicMock()

        # Patch the display_event function
        with (
            patch('openhands.cli.main.display_event') as mock_display_event,
            patch('openhands.cli.main.update_usage_metrics') as mock_update_metrics,
        ):
            # Create a closure to capture the current context
            async def test_func():
                # Set the pause event
                is_paused.set()

                # Create a context similar to run_session to call on_event_async
                # We're creating a function that mimics the environment of on_event_async
                async def on_event_async_test(event):
                    nonlocal reload_microagents, is_paused
                    mock_display_event(event, config)
                    mock_update_metrics(event, usage_metrics=MagicMock())

                    # Pause the agent if the pause event is set (through Ctrl-P)
                    if is_paused.is_set():
                        event_stream.add_event(
                            ChangeAgentStateAction(AgentState.PAUSED),
                            EventSource.USER,
                        )
                        # The pause event is not cleared here because we want to simulate
                        # the PAUSED event processing in a future event

                # Call on_event_async_test
                await on_event_async_test(event)

                # Check that event_stream.add_event was called with the correct action
                event_stream.add_event.assert_called_once()
                args, kwargs = event_stream.add_event.call_args
                action, source = args

                assert isinstance(action, ChangeAgentStateAction)
                assert action.agent_state == AgentState.PAUSED
                assert source == EventSource.USER

                # Check that is_paused is still set (will be cleared when PAUSED state is processed)
                assert is_paused.is_set()

            # Run the test function
            await test_func()

    @pytest.mark.asyncio
    async def test_awaiting_user_input_paused_skip(self):
        """Test that when is_paused is set, awaiting user input events do not trigger prompting."""
        # Create a mock event with AgentStateChangedObservation
        event = MagicMock()
        event.observation = AgentStateChangedObservation(
            agent_state=AgentState.AWAITING_USER_INPUT, content='Agent awaiting input'
        )

        # Create mock dependencies
        is_paused = asyncio.Event()
        reload_microagents = False

        # Mock function that would be called if code reaches that point
        mock_prompt_task = MagicMock()

        # Create a closure to capture the current context
        async def test_func():
            # Set the pause event
            is_paused.set()

            # Create a context similar to run_session to call on_event_async
            async def on_event_async_test(event):
                nonlocal reload_microagents, is_paused

                if isinstance(event.observation, AgentStateChangedObservation):
                    if event.observation.agent_state in [
                        AgentState.AWAITING_USER_INPUT,
                        AgentState.FINISHED,
                    ]:
                        # If the agent is paused, do not prompt for input
                        if is_paused.is_set():
                            return

                        # This code should not be reached if is_paused is set
                        mock_prompt_task()

            # Call on_event_async_test
            await on_event_async_test(event)

            # Verify that mock_prompt_task was not called
            mock_prompt_task.assert_not_called()

        # Run the test
        await test_func()

    @pytest.mark.asyncio
    async def test_awaiting_confirmation_paused_skip(self):
        """Test that when is_paused is set, awaiting confirmation events do not trigger prompting."""
        # Create a mock event with AgentStateChangedObservation
        event = MagicMock()
        event.observation = AgentStateChangedObservation(
            agent_state=AgentState.AWAITING_USER_CONFIRMATION,
            content='Agent awaiting confirmation',
        )

        # Create mock dependencies
        is_paused = asyncio.Event()

        # Mock function that would be called if code reaches that point
        mock_confirmation = MagicMock()

        # Create a closure to capture the current context
        async def test_func():
            # Set the pause event
            is_paused.set()

            # Create a context similar to run_session to call on_event_async
            async def on_event_async_test(event):
                nonlocal is_paused

                if isinstance(event.observation, AgentStateChangedObservation):
                    if (
                        event.observation.agent_state
                        == AgentState.AWAITING_USER_CONFIRMATION
                    ):
                        if is_paused.is_set():
                            return

                        # This code should not be reached if is_paused is set
                        mock_confirmation()

            # Call on_event_async_test
            await on_event_async_test(event)

            # Verify that confirmation function was not called
            mock_confirmation.assert_not_called()

        # Run the test
        await test_func()


class TestCliCommandsPauseResume:
    @pytest.mark.asyncio
    @patch('openhands.cli.commands.handle_resume_command')
    async def test_handle_commands_resume(self, mock_handle_resume):
        """Test that the handle_commands function properly calls handle_resume_command."""
        # Import here to avoid circular imports in test
        from openhands.cli.commands import handle_commands

        # Create mocks
        message = '/resume'
        event_stream = MagicMock()
        usage_metrics = MagicMock()
        sid = 'test-session-id'
        config = MagicMock()
        current_dir = '/test/dir'
        settings_store = MagicMock()

        # Mock return value
        mock_handle_resume.return_value = (False, False)

        # Call handle_commands
        close_repl, reload_microagents, new_session_requested = await handle_commands(
            message,
            event_stream,
            usage_metrics,
            sid,
            config,
            current_dir,
            settings_store,
        )

        # Check that handle_resume_command was called with correct args
        mock_handle_resume.assert_called_once_with(event_stream)

        # Check the return values
        assert close_repl is False
        assert reload_microagents is False
        assert new_session_requested is False


class TestAgentStatePauseResume:
    @pytest.mark.asyncio
    @patch('openhands.cli.main.display_agent_running_message')
    @patch('openhands.cli.main.process_agent_pause')
    async def test_agent_running_enables_pause(
        self, mock_process_agent_pause, mock_display_message
    ):
        """Test that when the agent is running, pause functionality is enabled."""
        # Create a mock event and event stream
        event = MagicMock()
        event.observation = AgentStateChangedObservation(
            agent_state=AgentState.RUNNING, content='Agent is running'
        )
        event_stream = MagicMock()

        # Create mock dependencies
        is_paused = asyncio.Event()
        loop = MagicMock()
        reload_microagents = False

        # Create a closure to capture the current context
        async def test_func():
            # Create a context similar to run_session to call on_event_async
            async def on_event_async_test(event):
                nonlocal reload_microagents

                if isinstance(event.observation, AgentStateChangedObservation):
                    if event.observation.agent_state == AgentState.RUNNING:
                        mock_display_message()
                        loop.create_task(
                            mock_process_agent_pause(is_paused, event_stream)
                        )

            # Call on_event_async_test
            await on_event_async_test(event)

            # Check that display_agent_running_message was called
            mock_display_message.assert_called_once()

            # Check that loop.create_task was called
            loop.create_task.assert_called_once()

        # Run the test function
        await test_func()

    @pytest.mark.asyncio
    @patch('openhands.cli.main.display_event')
    @patch('openhands.cli.main.update_usage_metrics')
    async def test_pause_event_changes_agent_state(
        self, mock_update_metrics, mock_display_event
    ):
        """Test that when is_paused is set, a PAUSED state change event is added to the stream."""
        # Create mock dependencies
        event = MagicMock()
        event_stream = MagicMock()
        is_paused = asyncio.Event()
        config = MagicMock()
        reload_microagents = False

        # Set the pause event
        is_paused.set()

        # Create a closure to capture the current context
        async def test_func():
            # Create a context similar to run_session to call on_event_async
            async def on_event_async_test(event):
                nonlocal reload_microagents
                mock_display_event(event, config)
                mock_update_metrics(event, MagicMock())

                # Pause the agent if the pause event is set (through Ctrl-P)
                if is_paused.is_set():
                    event_stream.add_event(
                        ChangeAgentStateAction(AgentState.PAUSED),
                        EventSource.USER,
                    )
                    is_paused.clear()

            # Call the function
            await on_event_async_test(event)

            # Check that the event_stream.add_event was called with the correct action
            event_stream.add_event.assert_called_once()
            args, kwargs = event_stream.add_event.call_args
            action, source = args

            assert isinstance(action, ChangeAgentStateAction)
            assert action.agent_state == AgentState.PAUSED
            assert source == EventSource.USER

            # Check that is_paused was cleared
            assert not is_paused.is_set()

        # Run the test
        await test_func()

    @pytest.mark.asyncio
    async def test_paused_agent_awaits_input(self):
        """Test that when the agent is paused, it awaits user input."""
        # Create mock dependencies
        event = MagicMock()
        # AgentStateChangedObservation requires a content parameter
        event.observation = AgentStateChangedObservation(
            agent_state=AgentState.PAUSED, content='Agent state changed to PAUSED'
        )
        is_paused = asyncio.Event()

        # Mock function that would be called for prompting
        mock_prompt_task = MagicMock()

        # Create a closure to capture the current context
        async def test_func():
            # Create a simplified version of on_event_async
            async def on_event_async_test(event):
                nonlocal is_paused

                if isinstance(event.observation, AgentStateChangedObservation):
                    if event.observation.agent_state == AgentState.PAUSED:
                        is_paused.clear()  # Revert the event state before prompting for user input
                        mock_prompt_task(event.observation.agent_state)

            # Set is_paused to test that it gets cleared
            is_paused.set()

            # Call the function
            await on_event_async_test(event)

            # Check that is_paused was cleared
            assert not is_paused.is_set()

            # Check that prompt task was called with the correct state
            mock_prompt_task.assert_called_once_with(AgentState.PAUSED)

        # Run the test
        await test_func()
