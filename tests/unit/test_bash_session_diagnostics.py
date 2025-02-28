"""Diagnostic tests for BashSession."""
import os
import time
from typing import List, Tuple

import pytest

from openhands.events.action import CmdRunAction
from openhands.runtime.utils.bash import BashSession


@pytest.fixture
def session():
    """Create a BashSession for testing."""
    session = BashSession(work_dir=os.getcwd())
    session.initialize()
    yield session
    session.close()


@pytest.fixture
def short_timeout_session():
    """Create a BashSession with short timeout for testing."""
    session = BashSession(work_dir=os.getcwd(), no_change_timeout_seconds=1)
    session.initialize()
    yield session
    session.close()


def test_command_output_filtering(session: BashSession):
    """Test that command output filtering is not too aggressive."""
    # Test various output patterns that should NOT be filtered
    test_cases = [
        'Line 1',  # Should be kept
        'Starting test command',  # Should be kept
        'inside if',  # Should be kept
        '[user input]',  # Should be kept
        'Hello world',  # Should be kept
        'Enter your name:',  # Should be kept
        'Line 40000',  # Should be kept
        'pid=123',  # Should be kept (when not in PS1 block)
        'exit_code=0',  # Should be kept (when not in PS1 block)
        '[Command]',  # Should be kept (when not a status message)
    ]

    for output in test_cases:
        # Use printf to avoid shell interpretation of brackets
        obs = session.execute(CmdRunAction(f'printf "{output}\\n"'))
        assert output in obs.content, f"Output '{output}' was incorrectly filtered"


def test_process_detection_states(session: BashSession):
    """Test that process detection logic correctly identifies different process states."""
    # Test different process states
    test_cases = [
        ('sleep 10', True),  # Long-running process
        ('echo "test"', False),  # Quick process
        ('python3 -c "while True: pass"', True),  # CPU-bound process
        ('cat', True),  # Interactive process
        ('exit 0', False),  # Completed process
    ]

    for cmd, should_be_running in test_cases:
        obs = session.execute(CmdRunAction(cmd, blocking=False))
        process_info = session.get_running_processes()
        
        # For quick processes, we need to check immediately
        if not should_be_running:
            assert process_info['is_command_running'] is False, f"Process for '{cmd}' should not be running"
            assert process_info['current_command_pid'] is None, f"Process for '{cmd}' should not have a PID"
            continue
            
        # For long-running processes, we need to check while they're running
        assert process_info['is_command_running'] is True, f"Process for '{cmd}' should be running"
        assert process_info['current_command_pid'] is not None, f"Process for '{cmd}' should have a PID"
        
        # Clean up the process
        session.execute(CmdRunAction('C-c', is_input=True))
        time.sleep(0.1)  # Give the process time to terminate


def test_ps1_metadata_handling(session: BashSession):
    """Test that PS1 metadata blocks are properly handled."""
    # Test different PS1 metadata block scenarios
    test_cases = [
        'echo "test"',  # Single command
        'for i in {1..3}; do echo $i; done',  # Loop
        'if true; then\necho "test"\nfi',  # Multi-line command
        'python3 -c "print(\'test\')"',  # Command with quotes
        'echo "###PS1JSON###"',  # Command containing PS1 markers
    ]

    for cmd in test_cases:
        obs = session.execute(CmdRunAction(cmd))
        # Check that PS1 metadata is properly parsed
        assert obs.metadata.exit_code == 0, f"Command '{cmd}' failed with exit code {obs.metadata.exit_code}"
        assert obs.metadata.username is not None, f"Username missing for command '{cmd}'"
        assert obs.metadata.hostname is not None, f"Hostname missing for command '{cmd}'"
        assert obs.metadata.working_dir is not None, f"Working directory missing for command '{cmd}'"
        assert obs.metadata.py_interpreter_path is not None, f"Python interpreter path missing for command '{cmd}'"


def test_output_truncation(session: BashSession):
    """Test that output truncation works correctly."""
    # Test different output sizes
    test_cases = [
        (100, False),  # Small output
        (1000, False),  # Medium output
        (10000, True),  # Large output
        (50000, True),  # Very large output
        (100000, True),  # Huge output
    ]

    for size, should_truncate in test_cases:
        cmd = f'for i in {{1..{size}}}; do echo "Line $i"; done'
        obs = session.execute(CmdRunAction(cmd))
        is_truncated = 'Previous command outputs are truncated' in obs.metadata.prefix
        assert is_truncated == should_truncate, f"Output truncation incorrect for size {size}"
        
        if should_truncate:
            # Should show some of the last lines
            last_line = f"Line {size}"
            assert last_line in obs.content, f"Last line missing for size {size}"


def test_command_continuation(short_timeout_session: BashSession):
    """Test that command continuation works correctly."""
    # Test different continuation scenarios
    test_cases: List[Tuple[str, List[str]]] = [
        ('for i in {1..3}; do echo $i; sleep 2; done', ['1', '2', '3']),  # Slow output
        ('python3 -c "import time; [print(i) or time.sleep(2) for i in range(3)]"', ['0', '1', '2']),  # Python with sleep
        ('yes | head -n 3', ['y', 'y', 'y']),  # Fast output with pipe
    ]

    for cmd, expected_output in test_cases:
        obs = short_timeout_session.execute(CmdRunAction(cmd, blocking=False))
        # Check initial output
        assert obs.metadata.exit_code == -1, f"Command '{cmd}' should still be running"
        
        # Get continuation output
        output_lines = []
        timeout = 10  # Maximum time to wait for command completion
        start_time = time.time()
        
        while obs.metadata.exit_code == -1 and time.time() - start_time < timeout:
            obs = short_timeout_session.execute(CmdRunAction('', is_input=True))  # Get more output
            if obs.content:
                output_lines.extend(obs.content.splitlines())
            time.sleep(0.1)  # Avoid busy waiting
        
        # Check final output contains all expected lines
        for line in expected_output:
            assert line in output_lines, f"Expected output '{line}' missing from command '{cmd}'"


def test_interactive_command_output(session: BashSession):
    """Test that interactive command output is properly handled."""
    # Test Python interactive input
    python_script = """name = input('Enter your name: '); age = input('Enter your age: '); print(f'Hello {name}, you are {age} years old')"""
    obs = session.execute(CmdRunAction(f'python3 -c "{python_script}"', blocking=False))

    # Wait for first prompt with timeout
    timeout = 10  # Maximum time to wait for command completion
    start_time = time.time()
    while 'Enter your name:' not in obs.content and time.time() - start_time < timeout:
        obs = session.execute(CmdRunAction('', is_input=True))  # Get more output
        time.sleep(0.1)  # Avoid busy waiting
    assert 'Enter your name:' in obs.content, "Python input prompt not found"

    # Send input and wait for second prompt
    obs = session.execute(CmdRunAction('Alice', is_input=True))
    start_time = time.time()
    while 'Enter your age:' not in obs.content and time.time() - start_time < timeout:
        obs = session.execute(CmdRunAction('', is_input=True))  # Get more output
        time.sleep(0.1)  # Avoid busy waiting
    assert 'Enter your age:' in obs.content, "Second input prompt not found"

    # Send second input and wait for final output
    obs = session.execute(CmdRunAction('25', is_input=True))
    start_time = time.time()
    while 'Hello Alice, you are 25 years old' not in obs.content and time.time() - start_time < timeout:
        obs = session.execute(CmdRunAction('', is_input=True))  # Get more output
        time.sleep(0.1)  # Avoid busy waiting
    assert 'Hello Alice, you are 25 years old' in obs.content, "Final output not found"


def test_command_output_with_special_characters(session: BashSession):
    """Test that command output with special characters is properly handled."""
    test_cases = [
        ('echo "###PS1JSON###"', '###PS1JSON###'),  # PS1 marker in output
        ('echo "[Command]"', '[Command]'),  # Command marker in output
        ('echo "pid=123"', 'pid=123'),  # Metadata-like output
        ('echo "Line 1\\nLine 2"', 'Line 1\nLine 2'),  # Multi-line output
        ('echo -e "\\033[31mred\\033[0m"', 'red'),  # ANSI color codes
        ('echo -e "\\t\\t\\tindented"', '\t\t\tindented'),  # Tabs
        ('echo "   spaced   "', '   spaced   '),  # Spaces
    ]

    for cmd, expected in test_cases:
        obs = session.execute(CmdRunAction(cmd))
        assert expected in obs.content, f"Output '{expected}' not found in command '{cmd}'"


def test_process_detection_edge_cases(session: BashSession):
    """Test process detection in edge cases."""
    test_cases = [
        # Process that forks and exits parent
        ('''python3 -c "import os, time; pid=os.fork(); os.system('sleep 5') if pid==0 else exit(0)"''', True),
        # Process that creates multiple children
        ('(sleep 5 & sleep 5 & sleep 5)', True),
        # Process that replaces itself
        ('exec sleep 5', True),
        # Process that creates a process group
        ('setsid sleep 5', True),
        # Quick process that might be missed
        ('sleep 0.1', False),
    ]

    for cmd, should_be_running in test_cases:
        obs = session.execute(CmdRunAction(cmd, blocking=False))
        process_info = session.get_running_processes()
        
        if not should_be_running:
            time.sleep(0.2)  # Wait for quick process to finish
            process_info = session.get_running_processes()
            assert process_info['is_command_running'] is False, f"Process for '{cmd}' should not be running"
            continue
            
        assert process_info['is_command_running'] is True, f"Process for '{cmd}' should be running"
        assert len(process_info['command_processes']) > 0, f"No processes found for '{cmd}'"
        
        # Clean up
        session.execute(CmdRunAction('C-c', is_input=True))
        time.sleep(0.1)