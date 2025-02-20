import pytest
import time
from openhands.events.action import CmdRunAction
from openhands.events.observation import CmdOutputObservation
from openhands.runtime.utils.bash import BashSession

def test_bash_session_stop_behavior():
    """Test that stopping a long-running process works correctly."""
    session = BashSession(work_dir="/tmp", no_change_timeout_seconds=1)
    session.initialize()

    # Start a long-running process that will timeout
    action = CmdRunAction(command="sleep 10")
    action.set_hard_timeout(2)  # Set a timeout so test doesn't hang
    action.blocking = False  # Allow no-change timeout
    
    # Execute the command and wait for timeout
    result = session.execute(action)
    assert isinstance(result, CmdOutputObservation)
    assert "command timed out" in result.metadata.suffix.lower() or "no new output" in result.metadata.suffix.lower()
    
    # Try to send a new command - this should fail since process is still running
    new_action = CmdRunAction(command="echo test")
    new_result = session.execute(new_action)
    assert isinstance(new_result, CmdOutputObservation)
    assert "previous command is still running" in new_result.metadata.suffix.lower()
    assert "not executed" in new_result.metadata.suffix.lower()

    # Try to send an empty command - this should show the running process output
    empty_action = CmdRunAction(command="")
    empty_result = session.execute(empty_action)
    assert isinstance(empty_result, CmdOutputObservation)
    assert "output of the previous command" in empty_result.metadata.prefix.lower()

    # Clean up
    session.close()

def test_bash_session_stop_command():
    """Test that sending C-c to stop a process works correctly."""
    session = BashSession(work_dir="/tmp", no_change_timeout_seconds=1)
    session.initialize()

    # Start a long-running process that will timeout
    action = CmdRunAction(command="sleep 10")
    action.set_hard_timeout(2)  # Set a timeout so test doesn't hang
    action.blocking = False  # Allow no-change timeout
    
    # Execute the command and wait for timeout
    result = session.execute(action)
    assert isinstance(result, CmdOutputObservation)
    assert "command timed out" in result.metadata.suffix.lower() or "no new output" in result.metadata.suffix.lower()
    
    # Send C-c to stop the process
    stop_action = CmdRunAction(command="C-c", is_input="true")
    stop_result = session.execute(stop_action)
    assert isinstance(stop_result, CmdOutputObservation)
    assert stop_result.metadata.exit_code == 130  # 130 is the exit code for SIGINT
    
    # Now we should be able to run a new command
    new_action = CmdRunAction(command="echo test")
    new_result = session.execute(new_action)
    assert isinstance(new_result, CmdOutputObservation)
    assert new_result.metadata.exit_code == 0
    assert "test" in new_result.content

    # Clean up
    session.close()