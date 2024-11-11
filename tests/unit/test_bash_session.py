import os

from openhands.core.logger import openhands_logger as logger
from openhands.events.action import CmdRunAction
from openhands.runtime.utils.bash import BashSession


def test_basic_command():
    session = BashSession(work_dir=os.getcwd())

    # Test simple command
    obs = session.execute(CmdRunAction("echo 'hello world'"))
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert obs.content.rstrip() == 'hello world'
    assert obs.metadata.exit_code == 0

    # Test command with error
    obs = session.execute(CmdRunAction('nonexistent_command'))
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert obs.metadata.exit_code == 127
    assert obs.content.rstrip() == 'bash: nonexistent_command: command not found'


def test_long_running_command():
    session = BashSession(work_dir=os.getcwd())

    # Test no-change timeout behavior
    obs = session.execute(CmdRunAction('sleep 15', blocking=False))
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert (
        f'no new output after {BashSession.NO_CHANGE_TIMEOUT_SECONDS} seconds'
        in obs.content
    )
    assert obs.metadata.exit_code is None

    # Continue waiting with empty command
    obs = session.execute(CmdRunAction(''))
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert '[Command output continued from previous command]' in obs.content

    # Start a long-running command
    obs = session.execute(CmdRunAction("sleep 2 && echo 'done sleeping'"))
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert 'done sleeping' in obs.content
    assert obs.metadata.exit_code == 0

    # Test timeout behavior
    obs = session.execute(CmdRunAction('sleep 5', timeout=1))
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
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
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert 'Enter name:' in obs.content
    assert obs.metadata.exit_code is None  # No exit code while waiting for input

    # Send input
    obs = session.execute(CmdRunAction('John'))
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert 'Hello John' in obs.content
    assert obs.metadata.exit_code == 0


def test_ctrl_c():
    session = BashSession(work_dir=os.getcwd())

    # Start infinite loop
    obs = session.execute(
        CmdRunAction("while true; do echo 'looping'; sleep 1; done", blocking=True)
    )
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert 'looping' in obs.content
    assert obs.metadata.exit_code is None  # No exit code while running

    # Send Ctrl+C
    obs = session.execute(CmdRunAction('ctrl+c'))
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert obs.metadata.exit_code == 130  # Standard exit code for Ctrl+C


def test_empty_command_errors():
    session = BashSession(work_dir=os.getcwd())

    # Test empty command without previous command
    obs = session.execute(CmdRunAction(''))
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert 'ERROR: No previous command to continue from' in obs.content
    assert obs.metadata.exit_code is None


def test_command_output_continuation():
    session = BashSession(work_dir=os.getcwd())

    # Start a command that produces output slowly
    obs = session.execute(
        CmdRunAction('for i in {1..5}; do echo $i; sleep 2; done', blocking=False)
    )
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert 'no new output after' in obs.content

    # Continue watching output
    obs = session.execute(CmdRunAction(''))
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert '[Command output continued from previous command]' in obs.content

    # Verify we can see new numbers in the output
    assert any(str(num) in obs.content for num in range(1, 6))
