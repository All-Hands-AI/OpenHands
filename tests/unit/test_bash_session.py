import os
import tempfile

from openhands.core.logger import openhands_logger as logger
from openhands.events.action import CmdRunAction
from openhands.runtime.utils.bash import BashCommandStatus, BashSession


def test_session_initialization():
    # Test with custom working directory
    with tempfile.TemporaryDirectory() as temp_dir:
        session = BashSession(work_dir=temp_dir)
        obs = session.execute(CmdRunAction('pwd'))
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})
        assert temp_dir in obs.content
        assert '[The command completed with exit code 0.]' in obs.content
        session.close()

    # Test with custom username
    session = BashSession(work_dir=os.getcwd(), username='nobody')
    assert 'openhands-nobody' in session.session.name
    session.close()


def test_pwd_property(tmp_path):
    session = BashSession(work_dir=tmp_path)
    # Change directory and verify pwd updates
    random_dir = tmp_path / 'random'
    random_dir.mkdir()
    session.execute(CmdRunAction(f'cd {random_dir}'))
    assert session.pwd == str(random_dir)
    session.close()


def test_basic_command():
    session = BashSession(work_dir=os.getcwd())

    # Test simple command
    obs = session.execute(CmdRunAction("echo 'hello world'"))
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert 'hello world' in obs.content
    assert '[The command completed with exit code 0.]' in obs.content
    assert obs.metadata.exit_code == 0
    assert session.prev_status == BashCommandStatus.COMPLETED

    # Test command with error
    obs = session.execute(CmdRunAction('nonexistent_command'))
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert obs.metadata.exit_code == 127
    assert 'bash: nonexistent_command: command not found' in obs.content
    assert '[The command completed with exit code 127.]' in obs.content
    assert session.prev_status == BashCommandStatus.COMPLETED

    # Test command with special characters
    obs = session.execute(CmdRunAction("echo 'hello   world    with\nspecial  chars'"))
    assert 'hello   world    with\nspecial  chars' in obs.content
    assert '[The command completed with exit code 0.]' in obs.content
    assert obs.metadata.exit_code == 0
    assert session.prev_status == BashCommandStatus.COMPLETED

    # Test multiple commands in sequence
    obs = session.execute(CmdRunAction('echo "first" && echo "second" && echo "third"'))
    assert 'first\nsecond\nthird' in obs.content
    assert '[The command completed with exit code 0.]' in obs.content
    assert obs.metadata.exit_code == 0
    assert session.prev_status == BashCommandStatus.COMPLETED

    session.close()


def test_long_running_command_follow_by_execute():
    session = BashSession(work_dir=os.getcwd(), no_change_timeout_seconds=2)

    # Test command that produces output slowly
    obs = session.execute(
        CmdRunAction('for i in {1..3}; do echo $i; sleep 3; done', blocking=False)
    )
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert '1' in obs.content  # First number should appear before timeout
    assert obs.metadata.exit_code == -1  # -1 indicates command is still running
    assert session.prev_status == BashCommandStatus.NO_CHANGE_TIMEOUT

    # Continue watching output
    obs = session.execute(CmdRunAction(''))
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert '[Command output continued from previous command]' in obs.content
    assert '2' in obs.content
    assert '[The command has no new output after 2 seconds.' in obs.content
    assert obs.metadata.exit_code == -1  # -1 indicates command is still running
    assert session.prev_status == BashCommandStatus.NO_CHANGE_TIMEOUT

    # Test command that produces no output
    obs = session.execute(CmdRunAction('sleep 15'))
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert '[Command output continued from previous command]' in obs.content
    assert '3' in obs.content
    assert '[The command has no new output after 2 seconds.' in obs.content
    assert obs.metadata.exit_code == -1  # -1 indicates command is still running
    assert session.prev_status == BashCommandStatus.NO_CHANGE_TIMEOUT

    session.close()


def test_interactive_command():
    session = BashSession(work_dir=os.getcwd(), no_change_timeout_seconds=3)

    # Test interactive command with blocking=True
    obs = session.execute(
        CmdRunAction(
            'read -p \'Enter name: \' name && echo "Hello $name"',
        )
    )
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert 'Enter name:' in obs.content
    assert obs.metadata.exit_code == -1  # -1 indicates command is still running
    assert session.prev_status == BashCommandStatus.NO_CHANGE_TIMEOUT

    # Send input
    obs = session.execute(CmdRunAction('John'))
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert 'Hello John' in obs.content
    assert obs.metadata.exit_code == 0
    assert '[The command completed with exit code 0.]' in obs.content
    assert session.prev_status == BashCommandStatus.COMPLETED

    # Test multiline command input
    obs = session.execute(CmdRunAction('cat << EOF'))
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert obs.metadata.exit_code == -1
    assert session.prev_status == BashCommandStatus.NO_CHANGE_TIMEOUT
    assert '[The command has no new output after 3 seconds.' in obs.content

    obs = session.execute(CmdRunAction('line 1'))
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert obs.metadata.exit_code == -1
    assert session.prev_status == BashCommandStatus.NO_CHANGE_TIMEOUT
    assert '[The command has no new output after 3 seconds.' in obs.content

    obs = session.execute(CmdRunAction('line 2'))
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert obs.metadata.exit_code == -1
    assert session.prev_status == BashCommandStatus.NO_CHANGE_TIMEOUT
    assert '[The command has no new output after 3 seconds.' in obs.content

    obs = session.execute(CmdRunAction('EOF'))
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert 'line 1\nline 2' in obs.content
    assert obs.metadata.exit_code == 0

    session.close()


def test_ctrl_c():
    session = BashSession(work_dir=os.getcwd(), no_change_timeout_seconds=2)

    # Start infinite loop
    obs = session.execute(
        CmdRunAction("while true; do echo 'looping'; sleep 3; done"),
    )
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert 'looping' in obs.content
    assert '[The command has no new output after 2 seconds.' in obs.content
    assert obs.metadata.exit_code == -1  # -1 indicates command is still running
    assert session.prev_status == BashCommandStatus.NO_CHANGE_TIMEOUT

    # Send Ctrl+C
    obs = session.execute(CmdRunAction('C-c'))
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert obs.metadata.exit_code == 1  # Standard exit code for Ctrl+C
    assert 'CTRL+C was sent.]' in obs.content
    assert session.prev_status == BashCommandStatus.COMPLETED

    session.close()


def test_empty_command_errors():
    session = BashSession(work_dir=os.getcwd())

    # Test empty command without previous command
    obs = session.execute(CmdRunAction(''))
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert 'ERROR: No previous command to continue from' in obs.content
    assert obs.metadata.exit_code == -1
    assert session.prev_status is None

    session.close()


def test_command_output_continuation():
    session = BashSession(work_dir=os.getcwd(), no_change_timeout_seconds=2)

    # Start a command that produces output slowly
    obs = session.execute(CmdRunAction('for i in {1..5}; do echo $i; sleep 3; done'))
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert 'no new output after' in obs.content
    assert session.prev_status == BashCommandStatus.NO_CHANGE_TIMEOUT

    obs = session.execute(CmdRunAction(''))
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert '[Command output continued from previous command]' in obs.content
    assert '2\n' in obs.content
    assert '[The command has no new output after 2 seconds.' in obs.content
    assert session.prev_status == BashCommandStatus.NO_CHANGE_TIMEOUT

    obs = session.execute(CmdRunAction(''))
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert '[Command output continued from previous command]' in obs.content
    assert '3\n' in obs.content
    assert '[The command has no new output after 2 seconds.' in obs.content
    assert session.prev_status == BashCommandStatus.NO_CHANGE_TIMEOUT

    obs = session.execute(CmdRunAction(''))
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert '[Command output continued from previous command]' in obs.content
    assert '4\n' in obs.content
    assert '[The command has no new output after 2 seconds.' in obs.content
    assert session.prev_status == BashCommandStatus.NO_CHANGE_TIMEOUT

    obs = session.execute(CmdRunAction(''))
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert '[Command output continued from previous command]' in obs.content
    assert '5\n' in obs.content
    assert '[The command has no new output after 2 seconds.' in obs.content
    assert session.prev_status == BashCommandStatus.NO_CHANGE_TIMEOUT

    obs = session.execute(CmdRunAction(''))
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert '[The command completed with exit code 0.]' in obs.content
    assert session.prev_status == BashCommandStatus.COMPLETED

    session.close()


def test_ansi_escape_codes():
    session = BashSession(work_dir=os.getcwd())

    # Test command that produces colored output
    obs = session.execute(
        CmdRunAction('echo -e "\\033[31mRed\\033[0m \\033[32mGreen\\033[0m"')
    )
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert 'Red Green' in obs.content  # ANSI codes should be stripped
    assert obs.metadata.exit_code == 0

    session.close()


def test_long_output():
    session = BashSession(work_dir=os.getcwd())

    # Generate a long output that may exceed buffer size
    obs = session.execute(CmdRunAction('for i in {1..1000}; do echo "Line $i"; done'))
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert 'Line 1' in obs.content
    assert 'Line 1000' in obs.content
    assert obs.metadata.exit_code == 0

    session.close()


def test_multiline_command():
    session = BashSession(work_dir=os.getcwd())

    # Test multiline command with PS2 prompt disabled
    obs = session.execute(
        CmdRunAction("""if true; then
echo "inside if"
fi""")
    )
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert 'inside if' in obs.content
    assert obs.metadata.exit_code == 0

    session.close()
