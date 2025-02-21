import asyncio
import time

from openhands.controller.agent import Agent
from openhands.controller.agent_controller import AgentController
from openhands.controller.state.state import State
from openhands.core.config import AgentConfig, LLMConfig
from openhands.core.message_utils import events_to_messages
from openhands.core.schema import AgentState
from openhands.events import EventStream
from openhands.events.action import CmdRunAction
from openhands.events.event import EventSource
from openhands.events.observation import CmdOutputObservation
from openhands.llm.llm import LLM
from openhands.runtime.utils.bash import BashSession
from openhands.storage.local import LocalFileStore


def test_bash_session_stop_behavior():
    """Test that stopping a long-running process works correctly."""
    session = BashSession(work_dir='/tmp', no_change_timeout_seconds=1)
    session.initialize()

    # Start a long-running process that will timeout
    action = CmdRunAction(command='sleep 10')
    action.set_hard_timeout(2)  # Set a timeout so test doesn't hang
    action.blocking = False  # Allow no-change timeout

    # Execute the command and wait for timeout
    result = session.execute(action)
    assert isinstance(result, CmdOutputObservation)
    assert (
        'command timed out' in result.metadata.suffix.lower()
        or 'no new output' in result.metadata.suffix.lower()
    )

    # Try to send a new command - this should fail since process is still running
    new_action = CmdRunAction(command='echo test')
    new_result = session.execute(new_action)
    assert isinstance(new_result, CmdOutputObservation)
    assert 'previous command is still running' in new_result.metadata.suffix.lower()
    assert 'not executed' in new_result.metadata.suffix.lower()

    # Try to send an empty command - this should show the running process output
    empty_action = CmdRunAction(command='')
    empty_result = session.execute(empty_action)
    assert isinstance(empty_result, CmdOutputObservation)
    assert 'output of the previous command' in empty_result.metadata.prefix.lower()

    # Clean up
    session.close()


def test_bash_session_stop_command():
    """Test that sending C-c to stop a process works correctly."""
    session = BashSession(work_dir='/tmp', no_change_timeout_seconds=1)
    session.initialize()

    # Start a long-running process that will timeout
    action = CmdRunAction(command='sleep 30')  # Make it longer to be more obvious
    action.set_hard_timeout(5)  # Set a timeout so test doesn't hang
    action.blocking = False  # Allow no-change timeout

    # Execute the command and wait for timeout
    result = session.execute(action)
    assert isinstance(result, CmdOutputObservation)
    assert (
        'command timed out' in result.metadata.suffix.lower()
        or 'no new output' in result.metadata.suffix.lower()
    )

    # Send C-c and measure how long it takes for the process to actually stop
    import time
    start_time = time.time()
    stop_action = CmdRunAction(command='C-c', is_input=True)
    stop_result = session.execute(stop_action)
    assert isinstance(stop_result, CmdOutputObservation)
    assert stop_result.metadata.exit_code == 130  # 130 is the exit code for SIGINT
    stop_time = time.time() - start_time
    print(f"\nTime taken to stop process: {stop_time:.3f} seconds")

    # Try to run a new command immediately to see if the process is actually stopped
    new_action = CmdRunAction(command='echo test')
    new_result = session.execute(new_action)
    assert isinstance(new_result, CmdOutputObservation)
    if 'previous command is still running' in new_result.metadata.suffix.lower():
        print("Process is still running!")
        assert False, "Process is still running after sending C-c"
    else:
        print("Process has been stopped")
    assert isinstance(new_result, CmdOutputObservation)
    assert new_result.metadata.exit_code == 0
    assert 'test' in new_result.content

    # Clean up
    session.close()


def test_agent_controller_stop():
    """Test that the agent controller sends C-c when stopping and the agent can process it."""
    # Create a mock event stream to capture events

    file_store = LocalFileStore('/tmp')
    event_stream = EventStream(sid='test', file_store=file_store)
    events = []

    def on_event(event):
        events.append(event)

    event_stream.subscribe('test', on_event, 'test')

    # Create a mock agent that processes events into messages
    class MockAgent(Agent):
        def step(self, state):
            # This is where the error would occur in the real agent
            # Try to process all events into messages
            # Process messages but don't use them - we just want to verify no error occurs
            _ = self._get_messages(state)
            return None

        def _get_messages(self, state):
            # Simulate what the real agent does - convert events to messages
            return events_to_messages(state.history)

    # Create a mock agent controller
    llm = LLM(config=LLMConfig())
    agent = MockAgent(llm=llm, config=AgentConfig())
    controller = AgentController(
        agent=agent,
        event_stream=event_stream,
        max_iterations=10,
        agent_configs={},
        agent_to_llm_config={},
        sid='test',
        confirmation_mode=False,
        headless_mode=True,
    )

    # Set up a pending action
    pending_action = CmdRunAction(command='sleep 30')  # Make it longer to be more obvious
    controller._pending_action = pending_action

    # Change state to STOPPED and measure how long it takes for the process to be killed
    import time
    start_time = time.time()
    asyncio.get_event_loop().run_until_complete(
        controller.set_agent_state_to(AgentState.STOPPED)
    )

    # Give the event stream time to process the event
    time.sleep(0.1)

    # Verify that C-c was sent and process was killed quickly
    stop_events = [
        e
        for e in events
        if isinstance(e, CmdRunAction)
        and e.command == 'C-c'
        and e.is_input is True
        and e.source == EventSource.USER
    ]
    assert len(stop_events) == 1, 'Expected exactly one C-c command to be sent'

    # Print all events for debugging
    print('\nAll events:')
    for e in events:
        print(
            f"Event: {type(e).__name__}, source={e.source}, command={getattr(e, 'command', None)}, is_input={getattr(e, 'is_input', None)}"
        )

    # Verify that the stop event can be converted to messages without error
    try:
        # Process messages but don't use them - we just want to verify no error occurs
        _ = events_to_messages(stop_events)
    except AssertionError as e:
        if 'Tool call metadata should NOT be None' in str(e):
            raise AssertionError(
                'The C-c command was sent without tool call metadata, which will cause an error when processing messages'
            ) from e
        raise

    # Verify that the agent can process the event history without error
    try:
        # Create a state with the stop event in history
        state = State()
        state.history = stop_events
        # Try to process the history - this would fail if the event is not properly marked as a user action
        agent.step(state)
    except AssertionError as e:
        if 'Tool call metadata should NOT be None' in str(e):
            raise AssertionError(
                'The agent failed to process the C-c command as a user action'
            ) from e
        raise
