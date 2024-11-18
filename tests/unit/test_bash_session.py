import os
import tempfile

from openhands.core.logger import openhands_logger as logger
from openhands.events.action import CmdRunAction
from openhands.events.observation import ErrorObservation
from openhands.runtime.utils.bash import BashCommandStatus, BashSession


def test_session_initialization():
    # Test with custom working directory
    with tempfile.TemporaryDirectory() as temp_dir:
        session = BashSession(work_dir=temp_dir)
        obs = session.execute(CmdRunAction('pwd'))
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})
        assert temp_dir in obs.content
        assert '[The command completed with exit code 0.]' in obs.metadata.suffix
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
    assert obs.metadata.suffix == '\n\n[The command completed with exit code 0.]'
    assert obs.metadata.prefix == ''
    assert obs.metadata.exit_code == 0
    assert session.prev_status == BashCommandStatus.COMPLETED

    # Test command with error
    obs = session.execute(CmdRunAction('nonexistent_command'))
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert obs.metadata.exit_code == 127
    assert 'bash: nonexistent_command: command not found' in obs.content
    assert obs.metadata.suffix == '\n\n[The command completed with exit code 127.]'
    assert obs.metadata.prefix == ''
    assert session.prev_status == BashCommandStatus.COMPLETED

    # Test command with special characters
    obs = session.execute(CmdRunAction("echo 'hello   world    with\nspecial  chars'"))
    assert 'hello   world    with\nspecial  chars' in obs.content
    assert obs.metadata.suffix == '\n\n[The command completed with exit code 0.]'
    assert obs.metadata.prefix == ''
    assert obs.metadata.exit_code == 0
    assert session.prev_status == BashCommandStatus.COMPLETED

    # Test multiple commands in sequence
    obs = session.execute(CmdRunAction('echo "first" && echo "second" && echo "third"'))
    assert 'first\nsecond\nthird' in obs.content
    assert obs.metadata.suffix == '\n\n[The command completed with exit code 0.]'
    assert obs.metadata.prefix == ''
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
    assert obs.metadata.suffix == (
        '\n\n[The command has no new output after 2 seconds. '
        "You may wait longer to see additional output by sending empty command '', "
        'send other commands to interact with the current process, '
        'or send keys to interrupt/kill the command.]'
    )
    assert obs.metadata.prefix == ''

    # Continue watching output
    obs = session.execute(CmdRunAction(''))
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert '2' in obs.content
    assert obs.metadata.prefix == '[Command output continued from previous command]\n'
    assert obs.metadata.suffix == (
        '\n\n[The command has no new output after 2 seconds. '
        "You may wait longer to see additional output by sending empty command '', "
        'send other commands to interact with the current process, '
        'or send keys to interrupt/kill the command.]'
    )
    assert obs.metadata.exit_code == -1  # -1 indicates command is still running
    assert session.prev_status == BashCommandStatus.NO_CHANGE_TIMEOUT

    # Test command that produces no output
    obs = session.execute(CmdRunAction('sleep 15'))
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert '3' in obs.content
    assert obs.metadata.prefix == '[Command output continued from previous command]\n'
    assert obs.metadata.suffix == (
        '\n\n[The command has no new output after 2 seconds. '
        "You may wait longer to see additional output by sending empty command '', "
        'send other commands to interact with the current process, '
        'or send keys to interrupt/kill the command.]'
    )
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
    assert obs.metadata.suffix == (
        '\n\n[The command has no new output after 3 seconds. '
        "You may wait longer to see additional output by sending empty command '', "
        'send other commands to interact with the current process, '
        'or send keys to interrupt/kill the command.]'
    )
    assert obs.metadata.prefix == ''

    # Send input
    obs = session.execute(CmdRunAction('John'))
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert 'Hello John' in obs.content
    assert obs.metadata.exit_code == 0
    assert obs.metadata.suffix == '\n\n[The command completed with exit code 0.]'
    assert obs.metadata.prefix == ''
    assert session.prev_status == BashCommandStatus.COMPLETED

    # Test multiline command input
    obs = session.execute(CmdRunAction('cat << EOF'))
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert obs.metadata.exit_code == -1
    assert session.prev_status == BashCommandStatus.NO_CHANGE_TIMEOUT
    assert obs.metadata.suffix == (
        '\n\n[The command has no new output after 3 seconds. '
        "You may wait longer to see additional output by sending empty command '', "
        'send other commands to interact with the current process, '
        'or send keys to interrupt/kill the command.]'
    )
    assert obs.metadata.prefix == ''

    obs = session.execute(CmdRunAction('line 1'))
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert obs.metadata.exit_code == -1
    assert session.prev_status == BashCommandStatus.NO_CHANGE_TIMEOUT
    assert obs.metadata.suffix == (
        '\n\n[The command has no new output after 3 seconds. '
        "You may wait longer to see additional output by sending empty command '', "
        'send other commands to interact with the current process, '
        'or send keys to interrupt/kill the command.]'
    )
    assert obs.metadata.prefix == '[Command output continued from previous command]\n'

    obs = session.execute(CmdRunAction('line 2'))
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert obs.metadata.exit_code == -1
    assert session.prev_status == BashCommandStatus.NO_CHANGE_TIMEOUT
    assert obs.metadata.suffix == (
        '\n\n[The command has no new output after 3 seconds. '
        "You may wait longer to see additional output by sending empty command '', "
        'send other commands to interact with the current process, '
        'or send keys to interrupt/kill the command.]'
    )
    assert obs.metadata.prefix == '[Command output continued from previous command]\n'

    obs = session.execute(CmdRunAction('EOF'))
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert 'line 1\nline 2' in obs.content
    assert obs.metadata.exit_code == 0
    assert obs.metadata.suffix == '\n\n[The command completed with exit code 0.]'
    assert obs.metadata.prefix == ''

    session.close()


def test_ctrl_c():
    session = BashSession(work_dir=os.getcwd(), no_change_timeout_seconds=2)

    # Start infinite loop
    obs = session.execute(
        CmdRunAction("while true; do echo 'looping'; sleep 3; done"),
    )
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert 'looping' in obs.content
    assert obs.metadata.suffix == (
        '\n\n[The command has no new output after 2 seconds. '
        "You may wait longer to see additional output by sending empty command '', "
        'send other commands to interact with the current process, '
        'or send keys to interrupt/kill the command.]'
    )
    assert obs.metadata.prefix == ''
    assert obs.metadata.exit_code == -1  # -1 indicates command is still running
    assert session.prev_status == BashCommandStatus.NO_CHANGE_TIMEOUT

    # Send Ctrl+C
    obs = session.execute(CmdRunAction('C-c'))
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert obs.metadata.exit_code == 130  # Standard exit code for Ctrl+C
    assert (
        obs.metadata.suffix
        == '\n\n[The command completed with exit code 130. CTRL+C was sent.]'
    )
    assert obs.metadata.prefix == ''
    assert session.prev_status == BashCommandStatus.COMPLETED

    session.close()


def test_empty_command_errors():
    session = BashSession(work_dir=os.getcwd())

    # Test empty command without previous command
    obs = session.execute(CmdRunAction(''))
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert (
        obs.content
        == 'ERROR: No previous command to continue from. Previous command has to be timeout to be continued.'
    )
    assert obs.metadata.exit_code == -1
    assert obs.metadata.prefix == ''
    assert obs.metadata.suffix == ''
    assert session.prev_status is None

    session.close()


def test_env_command():
    session = BashSession(work_dir=os.getcwd())

    # Test empty command without previous command
    obs = session.execute(CmdRunAction('env'))
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert 'PS1=###PS1JSON###' in obs.content
    assert 'PS2=' in obs.content
    assert obs.metadata.exit_code == 0
    assert obs.metadata.prefix == ''
    assert obs.metadata.suffix == '\n\n[The command completed with exit code 0.]'
    assert session.prev_status == BashCommandStatus.COMPLETED
    session.close()


def test_command_output_continuation():
    session = BashSession(work_dir=os.getcwd(), no_change_timeout_seconds=2)

    # Start a command that produces output slowly
    obs = session.execute(CmdRunAction('for i in {1..5}; do echo $i; sleep 3; done'))
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert obs.content == '1'
    assert obs.metadata.prefix == ''
    assert '[The command has no new output after 2 seconds.' in obs.metadata.suffix
    assert session.prev_status == BashCommandStatus.NO_CHANGE_TIMEOUT

    obs = session.execute(CmdRunAction(''))
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert '[Command output continued from previous command]' in obs.metadata.prefix
    assert obs.content == '2'
    assert '[The command has no new output after 2 seconds.' in obs.metadata.suffix
    assert session.prev_status == BashCommandStatus.NO_CHANGE_TIMEOUT

    obs = session.execute(CmdRunAction(''))
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert '[Command output continued from previous command]' in obs.metadata.prefix
    assert obs.content == '3'
    assert '[The command has no new output after 2 seconds.' in obs.metadata.suffix
    assert session.prev_status == BashCommandStatus.NO_CHANGE_TIMEOUT

    obs = session.execute(CmdRunAction(''))
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert '[Command output continued from previous command]' in obs.metadata.prefix
    assert obs.content == '4'
    assert '[The command has no new output after 2 seconds.' in obs.metadata.suffix
    assert session.prev_status == BashCommandStatus.NO_CHANGE_TIMEOUT

    obs = session.execute(CmdRunAction(''))
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert '[Command output continued from previous command]' in obs.metadata.prefix
    assert obs.content == '5'
    assert '[The command has no new output after 2 seconds.' in obs.metadata.suffix
    assert session.prev_status == BashCommandStatus.NO_CHANGE_TIMEOUT

    obs = session.execute(CmdRunAction(''))
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert '[The command completed with exit code 0.]' in obs.metadata.suffix
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
    assert obs.metadata.prefix == ''
    assert obs.metadata.suffix == '\n\n[The command completed with exit code 0.]'

    session.close()


def test_long_output():
    session = BashSession(work_dir=os.getcwd())

    # Generate a long output that may exceed buffer size
    obs = session.execute(CmdRunAction('for i in {1..1000}; do echo "Line $i"; done'))
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert 'Line 1' in obs.content
    assert 'Line 1000' in obs.content
    assert obs.metadata.exit_code == 0
    assert obs.metadata.prefix == ''
    assert obs.metadata.suffix == '\n\n[The command completed with exit code 0.]'

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
    assert obs.metadata.prefix == ''
    assert obs.metadata.suffix == '\n\n[The command completed with exit code 0.]'

    session.close()


def test_multiple_multiline_commands():
    session = BashSession(work_dir=os.getcwd())
    try:
        cmds = [
            'ls -l',
            'echo -e "hello\nworld"',
            """echo -e "hello it's me\"""",
            """echo \\
        -e 'hello' \\
        -v""",
            """echo -e 'hello\\nworld\\nare\\nyou\\nthere?'""",
            """echo -e 'hello\nworld\nare\nyou\n\nthere?'""",
            """echo -e 'hello\nworld "'""",
        ]
        joined_cmds = '\n'.join(cmds)

        # Test that running multiple commands at once fails
        obs = session.execute(CmdRunAction(joined_cmds))
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})
        assert isinstance(obs, ErrorObservation)
        assert 'Cannot execute multiple commands at once' in obs.content

        # Now run each command individually and verify they work
        results = []
        for cmd in cmds:
            obs = session.execute(CmdRunAction(cmd))
            logger.info(obs, extra={'msg_type': 'OBSERVATION'})
            assert obs.metadata.exit_code == 0
            assert obs.metadata.prefix == ''
            assert (
                obs.metadata.suffix == '\n\n[The command completed with exit code 0.]'
            )
            results.append(obs.content)

        # Verify all expected outputs are present
        assert 'total' in results[0]  # ls -l
        assert 'hello\nworld' in results[1]  # echo -e "hello\nworld"
        assert "hello it's me" in results[2]  # echo -e "hello it\'s me"
        assert 'hello -v' in results[3]  # echo -e 'hello' -v
        assert (
            'hello\nworld\nare\nyou\nthere?' in results[4]
        )  # echo -e 'hello\nworld\nare\nyou\nthere?'
        assert (
            'hello\nworld\nare\nyou\n\nthere?' in results[5]
        )  # echo -e with literal newlines
        assert 'hello\nworld "' in results[6]  # echo -e with quote
    finally:
        session.close()
