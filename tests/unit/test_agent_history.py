from unittest.mock import patch

from openhands.controller.agent_controller import AgentController
from openhands.controller.state.state import State
from openhands.events.action.commands import CmdRunAction
from openhands.events.action.message import MessageAction
from openhands.events.event import EventSource
from openhands.events.observation.commands import CmdOutputObservation


def test_apply_conversation_window_basic(mock_event_stream, mock_agent):
    """Test that the _apply_conversation_window method correctly prunes a list of events."""
    controller = AgentController(
        agent=mock_agent,
        event_stream=mock_event_stream,
        max_iterations=10,
        sid='test_apply_conversation_window_basic',
        confirmation_mode=False,
        headless_mode=True,
    )

    # Create a sequence of events with IDs
    first_msg = MessageAction(content='Hello, start task', wait_for_response=False)
    first_msg._source = EventSource.USER
    first_msg._id = 1

    # Add agent question
    agent_msg = MessageAction(
        content='What task would you like me to perform?', wait_for_response=True
    )
    agent_msg._source = EventSource.AGENT
    agent_msg._id = 2

    # Add user response
    user_response = MessageAction(
        content='Please list all files and show me current directory',
        wait_for_response=False,
    )
    user_response._source = EventSource.USER
    user_response._id = 3

    cmd1 = CmdRunAction(command='ls')
    cmd1._id = 4
    obs1 = CmdOutputObservation(command='ls', content='file1.txt', command_id=4)
    obs1._id = 5
    obs1._cause = 4

    cmd2 = CmdRunAction(command='pwd')
    cmd2._id = 6
    obs2 = CmdOutputObservation(command='pwd', content='/home', command_id=6)
    obs2._id = 7
    obs2._cause = 6

    events = [first_msg, agent_msg, user_response, cmd1, obs1, cmd2, obs2]
    controller.state.history = (
        events.copy()
    )  # Keep assigning to history if needed for state setup
    controller.state.start_id = events[0].id  # Ensure start_id is set correctly

    # Apply truncation, mocking the method that causes the error
    with patch.object(controller, '_first_user_message', return_value=first_msg):
        truncated = controller._apply_conversation_window()

    # Verify truncation occured
    # Should keep first user message and roughly half of other events
    assert (
        3 <= len(truncated) < len(events)
    )  # First message + at least one action-observation pair
    assert truncated[0] == first_msg  # First message always preserved
    # Check start_id remains the same after truncation if first_msg is kept
    # Note: _apply_conversation_window doesn't modify state.start_id directly,
    # it returns the list. The caller (like _handle_long_context_error) would update state.
    # So we assert based on the initial state setup.
    assert controller.state.start_id == first_msg._id

    # Verify pairs aren't split
    for i, event in enumerate(truncated[1:]):
        if isinstance(event, CmdOutputObservation):
            assert any(e._id == event._cause for e in truncated[: i + 1])


def test_history_restoration_after_truncation(mock_event_stream, mock_agent):
    controller = AgentController(
        agent=mock_agent,
        event_stream=mock_event_stream,
        max_iterations=10,
        sid='test_truncation',
        confirmation_mode=False,
        headless_mode=True,
    )

    # Create events with IDs
    first_msg = MessageAction(content='Start task', wait_for_response=False)
    first_msg._source = EventSource.USER
    first_msg._id = 1

    events = [first_msg]
    for i in range(5):
        cmd = CmdRunAction(command=f'cmd{i}')
        cmd._id = i + 2
        obs = CmdOutputObservation(
            command=f'cmd{i}', content=f'output{i}', command_id=cmd._id
        )
        obs._cause = cmd._id
        events.extend([cmd, obs])

    # Set up initial history
    controller.state.history = events.copy()
    controller.state.start_id = events[0].id  # Ensure start_id is set correctly

    # Force truncation, mocking the method that causes the error
    with patch.object(controller, '_first_user_message', return_value=first_msg):
        # The method returns the truncated list, assign it back to history for the test setup
        controller.state.history = controller._apply_conversation_window()

    # Save state details needed for restoration check
    saved_start_id = controller.state.start_id  # Should still be 1
    saved_history_after_truncation = controller.state.history.copy()
    saved_history_len = len(saved_history_after_truncation)

    # Set up mock event stream for new controller to simulate loading truncated history
    mock_event_stream.get_events.return_value = saved_history_after_truncation

    # Create new controller instance to simulate loading state
    new_controller = AgentController(
        agent=mock_agent,
        event_stream=mock_event_stream,
        max_iterations=10,
        sid='test_truncation',  # Use same SID if simulating reload
        confirmation_mode=False,
        headless_mode=True,
        # Pass minimal state, history will be loaded via _init_history
        initial_state=State(session_id='test_truncation', start_id=saved_start_id),
    )
    # _init_history is called during AgentController.__init__ if state.history is empty
    # Since we passed initial_state without history, it should have loaded via mock_event_stream

    # Verify restoration
    assert len(new_controller.state.history) == saved_history_len
    assert (
        new_controller.state.history[0] == first_msg
    )  # First message should be preserved
    assert new_controller.state.start_id == saved_start_id  # Start ID should match
