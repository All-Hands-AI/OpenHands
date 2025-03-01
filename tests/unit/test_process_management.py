"""Tests for process management functionality."""

import os
import time

from openhands.events.action import CmdRunAction, StopProcessesAction
from openhands.runtime.utils.bash import BashSession


def test_multiple_processes():
    """Test handling multiple processes running simultaneously."""
    session = BashSession(work_dir=os.getcwd(), no_change_timeout_seconds=2)
    session.initialize()

    # Start multiple background processes
    obs = session.execute(CmdRunAction('sleep 60 & sleep 70 & sleep 80 &'))
    assert obs.metadata.exit_code == 0

    # Check that all processes are tracked
    process_info = session.get_running_processes()
    assert process_info['is_command_running'] is True
    assert len(process_info['command_processes']) >= 3  # At least 3 sleep processes

    # Stop all processes
    obs = session.execute(StopProcessesAction())
    assert 'All running processes have been terminated' in obs.content

    # Verify all processes are stopped
    process_info = session.get_running_processes()
    assert process_info['is_command_running'] is False
    assert len(process_info['command_processes']) == 0

    session.close()


def test_nested_processes():
    """Test handling nested processes."""
    session = BashSession(work_dir=os.getcwd(), no_change_timeout_seconds=2)
    session.initialize()

    # Start a process that spawns other processes
    obs = session.execute(
        CmdRunAction('bash -c "while true; do sleep 1 & sleep 2 & sleep 3; done" &')
    )
    assert obs.metadata.exit_code == 0

    time.sleep(2)  # Give time for processes to spawn

    # Check that parent and child processes are tracked
    process_info = session.get_running_processes()
    assert process_info['is_command_running'] is True
    assert (
        len(process_info['command_processes']) >= 4
    )  # bash + at least 3 sleep processes

    # Stop all processes
    obs = session.execute(StopProcessesAction())
    assert 'All running processes have been terminated' in obs.content

    # Verify all processes are stopped
    process_info = session.get_running_processes()
    assert process_info['is_command_running'] is False
    assert len(process_info['command_processes']) == 0

    session.close()


def test_process_termination_signals():
    """Test process termination with different signals."""
    session = BashSession(work_dir=os.getcwd(), no_change_timeout_seconds=2)
    session.initialize()

    # Start a process that ignores SIGTERM
    obs = session.execute(
        CmdRunAction(
            'python3 -c "import signal, time; signal.signal(signal.SIGTERM, signal.SIG_IGN); time.sleep(60)" &'
        )
    )
    assert obs.metadata.exit_code == 0

    time.sleep(1)  # Give time for process to start

    # Check that process is running
    process_info = session.get_running_processes()
    assert process_info['is_command_running'] is True
    assert len(process_info['command_processes']) >= 1

    # Stop all processes (should use SIGKILL for stubborn processes)
    obs = session.execute(StopProcessesAction())
    assert 'All running processes have been terminated' in obs.content

    # Verify process is stopped
    process_info = session.get_running_processes()
    assert process_info['is_command_running'] is False
    assert len(process_info['command_processes']) == 0

    session.close()


def test_process_tracking_edge_cases():
    """Test edge cases in process tracking."""
    session = BashSession(work_dir=os.getcwd(), no_change_timeout_seconds=2)
    session.initialize()

    # Test very short-lived process
    obs = session.execute(CmdRunAction('sleep 0.1'))
    assert obs.metadata.exit_code == 0

    # Process should complete before we can track it
    process_info = session.get_running_processes()
    assert process_info['is_command_running'] is False
    assert len(process_info['command_processes']) == 0

    # Test process that exits immediately
    obs = session.execute(CmdRunAction('exit 0'))
    assert obs.metadata.exit_code == 0

    process_info = session.get_running_processes()
    assert process_info['is_command_running'] is False
    assert len(process_info['command_processes']) == 0

    # Test process that forks and exits
    obs = session.execute(CmdRunAction('(sleep 30 &) && exit 0'))
    assert obs.metadata.exit_code == 0

    time.sleep(1)  # Give time for fork to complete

    # The sleep process should still be tracked
    process_info = session.get_running_processes()
    assert process_info['is_command_running'] is True
    assert len(process_info['command_processes']) >= 1

    # Stop all processes
    obs = session.execute(StopProcessesAction())
    assert 'All running processes have been terminated' in obs.content

    session.close()


def test_stop_processes_idempotency():
    """Test that StopProcessesAction is idempotent."""
    session = BashSession(work_dir=os.getcwd(), no_change_timeout_seconds=2)
    session.initialize()

    # First call with no processes running
    obs = session.execute(StopProcessesAction())
    assert 'No processes were terminated' in obs.content

    # Start some processes
    session.execute(CmdRunAction('sleep 60 & sleep 70 &'))
    time.sleep(1)

    # First stop - should terminate processes
    obs = session.execute(StopProcessesAction())
    assert 'All running processes have been terminated' in obs.content

    # Second stop - should be safe to call
    obs = session.execute(StopProcessesAction())
    assert 'No processes were terminated' in obs.content

    session.close()
