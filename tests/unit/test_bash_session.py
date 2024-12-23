import os
import tempfile

from openhands.core.logger import openhands_logger as logger
from openhands.events.action import CmdRunAction
from openhands.runtime.utils.bash import BashCommandStatus, BashSession


def test_session_initialization():
    # Test with custom working directory
    with tempfile.TemporaryDirectory() as temp_dir:
        session = BashSession(work_dir=temp_dir)
        session.initialize()
        obs = session.execute(CmdRunAction('pwd'))
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})
        assert temp_dir in obs.content
        assert '[The command completed with exit code 0.]' in obs.metadata.suffix
        session.close()

    # Test with custom username
    session = BashSession(work_dir=os.getcwd(), username='nobody')
    session.initialize()
    assert 'openhands-nobody' in session.session.name
    session.close()


def test_cwd_property(tmp_path):
    session = BashSession(work_dir=tmp_path)
    session.initialize()
    # Change directory and verify pwd updates
    random_dir = tmp_path / 'random'
    random_dir.mkdir()
    session.execute(CmdRunAction(f'cd {random_dir}'))
    assert session.cwd == str(random_dir)
    session.close()


def test_basic_command():
    session = BashSession(work_dir=os.getcwd())
    session.initialize()

    # Test simple command
    obs = session.execute(CmdRunAction("echo 'hello world'"))
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert 'hello world' in obs.content
    assert obs.metadata.suffix == '\n[The command completed with exit code 0.]'
    assert obs.metadata.prefix == ''
    assert obs.metadata.exit_code == 0
    assert session.prev_status == BashCommandStatus.COMPLETED

    # Test command with error
    obs = session.execute(CmdRunAction('nonexistent_command'))
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert obs.metadata.exit_code == 127
    assert 'nonexistent_command: command not found' in obs.content
    assert obs.metadata.suffix == '\n[The command completed with exit code 127.]'
    assert obs.metadata.prefix == ''
    assert session.prev_status == BashCommandStatus.COMPLETED

    # Test multiple commands in sequence
    obs = session.execute(CmdRunAction('echo "first" && echo "second" && echo "third"'))
    assert 'first' in obs.content
    assert 'second' in obs.content
    assert 'third' in obs.content
    assert obs.metadata.suffix == '\n[The command completed with exit code 0.]'
    assert obs.metadata.prefix == ''
    assert obs.metadata.exit_code == 0
    assert session.prev_status == BashCommandStatus.COMPLETED

    session.close()


def test_long_running_command_follow_by_execute():
    session = BashSession(work_dir=os.getcwd(), no_change_timeout_seconds=2)
    session.initialize()

    # Test command that produces output slowly
    obs = session.execute(
        CmdRunAction('for i in {1..3}; do echo $i; sleep 3; done', blocking=False)
    )
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert '1' in obs.content  # First number should appear before timeout
    assert obs.metadata.exit_code == -1  # -1 indicates command is still running
    assert session.prev_status == BashCommandStatus.NO_CHANGE_TIMEOUT
    assert obs.metadata.suffix == (
        '\n[The command has no new output after 2 seconds. '
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
        '\n[The command has no new output after 2 seconds. '
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
        '\n[The command has no new output after 2 seconds. '
        "You may wait longer to see additional output by sending empty command '', "
        'send other commands to interact with the current process, '
        'or send keys to interrupt/kill the command.]'
    )
    assert obs.metadata.exit_code == -1  # -1 indicates command is still running
    assert session.prev_status == BashCommandStatus.NO_CHANGE_TIMEOUT

    session.close()


def test_interactive_command():
    session = BashSession(work_dir=os.getcwd(), no_change_timeout_seconds=3)
    session.initialize()

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
        '\n[The command has no new output after 3 seconds. '
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
    assert obs.metadata.suffix == '\n[The command completed with exit code 0.]'
    assert obs.metadata.prefix == ''
    assert session.prev_status == BashCommandStatus.COMPLETED

    # Test multiline command input
    obs = session.execute(CmdRunAction('cat << EOF'))
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert obs.metadata.exit_code == -1
    assert session.prev_status == BashCommandStatus.NO_CHANGE_TIMEOUT
    assert obs.metadata.suffix == (
        '\n[The command has no new output after 3 seconds. '
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
        '\n[The command has no new output after 3 seconds. '
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
        '\n[The command has no new output after 3 seconds. '
        "You may wait longer to see additional output by sending empty command '', "
        'send other commands to interact with the current process, '
        'or send keys to interrupt/kill the command.]'
    )
    assert obs.metadata.prefix == '[Command output continued from previous command]\n'

    obs = session.execute(CmdRunAction('EOF'))
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert 'line 1' in obs.content and 'line 2' in obs.content
    assert obs.metadata.exit_code == 0
    assert obs.metadata.suffix == '\n[The command completed with exit code 0.]'
    assert obs.metadata.prefix == ''

    session.close()


def test_ctrl_c():
    session = BashSession(work_dir=os.getcwd(), no_change_timeout_seconds=2)
    session.initialize()

    # Start infinite loop
    obs = session.execute(
        CmdRunAction("while true; do echo 'looping'; sleep 3; done"),
    )
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert 'looping' in obs.content
    assert obs.metadata.suffix == (
        '\n[The command has no new output after 2 seconds. '
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
        == '\n[The command completed with exit code 130. CTRL+C was sent.]'
    )
    assert obs.metadata.prefix == ''
    assert session.prev_status == BashCommandStatus.COMPLETED

    session.close()


def test_empty_command_errors():
    session = BashSession(work_dir=os.getcwd())
    session.initialize()

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


def test_command_output_continuation():
    session = BashSession(work_dir=os.getcwd(), no_change_timeout_seconds=2)
    session.initialize()

    # Start a command that produces output slowly
    obs = session.execute(CmdRunAction('for i in {1..5}; do echo $i; sleep 3; done'))
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert obs.content.strip() == '1'
    assert obs.metadata.prefix == ''
    assert '[The command has no new output after 2 seconds.' in obs.metadata.suffix
    assert session.prev_status == BashCommandStatus.NO_CHANGE_TIMEOUT

    obs = session.execute(CmdRunAction(''))
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert '[Command output continued from previous command]' in obs.metadata.prefix
    assert obs.content.strip() == '2'
    assert '[The command has no new output after 2 seconds.' in obs.metadata.suffix
    assert session.prev_status == BashCommandStatus.NO_CHANGE_TIMEOUT

    obs = session.execute(CmdRunAction(''))
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert '[Command output continued from previous command]' in obs.metadata.prefix
    assert obs.content.strip() == '3'

    assert '[The command has no new output after 2 seconds.' in obs.metadata.suffix
    assert session.prev_status == BashCommandStatus.NO_CHANGE_TIMEOUT

    obs = session.execute(CmdRunAction(''))
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert '[Command output continued from previous command]' in obs.metadata.prefix
    assert obs.content.strip() == '4'
    assert '[The command has no new output after 2 seconds.' in obs.metadata.suffix
    assert session.prev_status == BashCommandStatus.NO_CHANGE_TIMEOUT

    obs = session.execute(CmdRunAction(''))
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert '[Command output continued from previous command]' in obs.metadata.prefix
    assert obs.content.strip() == '5'
    assert '[The command has no new output after 2 seconds.' in obs.metadata.suffix
    assert session.prev_status == BashCommandStatus.NO_CHANGE_TIMEOUT

    obs = session.execute(CmdRunAction(''))
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert '[The command completed with exit code 0.]' in obs.metadata.suffix
    assert session.prev_status == BashCommandStatus.COMPLETED

    session.close()


def test_long_output():
    session = BashSession(work_dir=os.getcwd())
    session.initialize()

    # Generate a long output that may exceed buffer size
    obs = session.execute(CmdRunAction('for i in {1..5000}; do echo "Line $i"; done'))
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert 'Line 1' in obs.content
    assert 'Line 5000' in obs.content
    assert obs.metadata.exit_code == 0
    assert obs.metadata.prefix == ''
    assert obs.metadata.suffix == '\n[The command completed with exit code 0.]'

    session.close()


def test_long_output_exceed_history_limit():
    session = BashSession(work_dir=os.getcwd())
    session.initialize()

    # Generate a long output that may exceed buffer size
    obs = session.execute(CmdRunAction('for i in {1..50000}; do echo "Line $i"; done'))
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert 'Previous command outputs are truncated' in obs.metadata.prefix
    assert 'Line 40000' in obs.content
    assert 'Line 50000' in obs.content
    assert obs.metadata.exit_code == 0
    assert obs.metadata.suffix == '\n[The command completed with exit code 0.]'

    session.close()


def test_multiline_command():
    session = BashSession(work_dir=os.getcwd())
    session.initialize()

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
    assert obs.metadata.suffix == '\n[The command completed with exit code 0.]'

    session.close()


def test_python_interactive_input():
    session = BashSession(work_dir=os.getcwd(), no_change_timeout_seconds=2)
    session.initialize()

    # Test Python program that asks for input - properly escaped for bash
    python_script = """name = input('Enter your name: '); age = input('Enter your age: '); print(f'Hello {name}, you are {age} years old')"""

    # Start Python with the interactive script
    obs = session.execute(CmdRunAction(f'python3 -c "{python_script}"'))
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert 'Enter your name:' in obs.content
    assert obs.metadata.exit_code == -1  # -1 indicates command is still running
    assert session.prev_status == BashCommandStatus.NO_CHANGE_TIMEOUT

    # Send first input (name)
    obs = session.execute(CmdRunAction('Alice'))
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert 'Enter your age:' in obs.content
    assert obs.metadata.exit_code == -1
    assert session.prev_status == BashCommandStatus.NO_CHANGE_TIMEOUT

    # Send second input (age)
    obs = session.execute(CmdRunAction('25'))
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert 'Hello Alice, you are 25 years old' in obs.content
    assert obs.metadata.exit_code == 0
    assert obs.metadata.suffix == '\n[The command completed with exit code 0.]'
    assert session.prev_status == BashCommandStatus.COMPLETED

    session.close()
