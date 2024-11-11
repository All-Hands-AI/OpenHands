import os

from openhands.events.action import CmdRunAction
from openhands.runtime.utils.bash import BashSession


def test_basic_command():
    session = BashSession(work_dir=os.getcwd())

    # Test simple command
    obs = session.execute(CmdRunAction("echo 'hello world'"))
    assert 'hello world' in obs.content
    assert obs.metadata.exit_code == 0

    # Test command with error
    obs = session.execute(CmdRunAction('nonexistent_command'))
    assert obs.metadata.exit_code != 0
    assert 'command not found' in obs.content.lower()


def test_long_running_command():
    session = BashSession(work_dir=os.getcwd())

    # Start a long-running command
    obs = session.execute(CmdRunAction("sleep 2 && echo 'done sleeping'"))
    assert 'done sleeping' in obs.content
    assert obs.metadata.exit_code == 0

    # Test timeout behavior
    obs = session.execute(CmdRunAction('sleep 5', timeout=1))
    assert 'timed out after 1 seconds' in obs.content
    assert obs.metadata.exit_code is None  # No exit code available for timeout


def test_interactive_command():
    session = BashSession(work_dir=os.getcwd())

    # Test interactive command with blocking=True
    obs = session.execute(
        CmdRunAction(
            'read -p \'Enter name: \' name && echo "Hello $name"', blocking=True
        )
    )
    assert 'Enter name:' in obs.content
    assert obs.metadata.exit_code is None  # No exit code while waiting for input

    # Send input
    obs = session.execute(CmdRunAction('John'))
    assert 'Hello John' in obs.content
    assert obs.metadata.exit_code == 0


def test_ctrl_c():
    session = BashSession(work_dir=os.getcwd())

    # Start infinite loop
    obs = session.execute(
        CmdRunAction("while true; do echo 'looping'; sleep 1; done", blocking=True)
    )
    assert 'looping' in obs.content
    assert obs.metadata.exit_code is None  # No exit code while running

    # Send Ctrl+C
    obs = session.execute(CmdRunAction('ctrl+c'))
    assert obs.metadata.exit_code == 130  # Standard exit code for Ctrl+C
