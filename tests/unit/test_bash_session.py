import os

from openhands.events.action import CmdRunAction
from openhands.runtime.utils.bash import BashSession


def test_basic_command():
    session = BashSession(work_dir=os.getcwd())

    # Test simple command
    result = session.execute(CmdRunAction("echo 'hello world'"))
    assert 'hello world' in result.output
    assert result.metadata.exit_code == 0

    # Test command with error
    result = session.execute(CmdRunAction('nonexistent_command'))
    assert result.metadata.exit_code != 0
    assert 'command not found' in result.output.lower()


def test_long_running_command():
    session = BashSession(work_dir=os.getcwd())

    # Start a long-running command
    result = session.execute(CmdRunAction("sleep 2 && echo 'done sleeping'"))
    assert 'done sleeping' in result.output
    assert result.metadata.exit_code == 0

    # Test timeout behavior
    result = session.execute(CmdRunAction('sleep 5', timeout=1))
    assert 'timed out after 1 seconds' in result.output
    assert result.metadata.exit_code is None  # No exit code available for timeout


def test_interactive_command():
    session = BashSession(work_dir=os.getcwd())

    # Test interactive command with blocking=True
    result = session.execute(
        CmdRunAction(
            'read -p \'Enter name: \' name && echo "Hello $name"', blocking=True
        )
    )
    assert 'Enter name:' in result.output
    assert result.metadata.exit_code is None  # No exit code while waiting for input

    # Send input
    result = session.execute(CmdRunAction('John'))
    assert 'Hello John' in result.output
    assert result.metadata.exit_code == 0


def test_ctrl_c():
    session = BashSession(work_dir=os.getcwd())

    # Start infinite loop
    result = session.execute(
        CmdRunAction("while true; do echo 'looping'; sleep 1; done", blocking=True)
    )
    assert 'looping' in result.output
    assert result.metadata.exit_code is None  # No exit code while running

    # Send Ctrl+C
    result = session.execute(CmdRunAction('ctrl+c'))
    assert result.metadata.exit_code == 130  # Standard exit code for Ctrl+C
