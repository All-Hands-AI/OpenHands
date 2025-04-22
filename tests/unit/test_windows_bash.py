import os
import sys
import pytest
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch
import time

# The main module (windows_bash.py) handles SDK loading and potential errors.
# Tests should not attempt to load the SDK themselves.
# If loading fails in the main module, the session class will raise an error on init.

# Import the class under test
from openhands.runtime.utils.windows_bash import WindowsPowershellSession
from openhands.events.action import CmdRunAction
from openhands.events.observation.commands import CmdOutputObservation, CmdOutputMetadata
from openhands.events.observation import ErrorObservation

# Skip all tests in this module if not running on Windows
pytestmark = pytest.mark.skipif(sys.platform != 'win32', reason="WindowsPowershellSession tests require Windows")


@pytest.fixture
def temp_work_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
def windows_bash_session(temp_work_dir):
    """Create a WindowsPowershellSession instance for testing."""
    # Instantiate the class. Initialization happens in __init__.
    session = WindowsPowershellSession(
        work_dir=temp_work_dir,
        username=None,
    )
    assert session._initialized # Should be true after __init__
    yield session
    # Ensure cleanup happens even if test fails
    session.close()


def test_initialization(windows_bash_session, temp_work_dir):
    """Test that the session initializes correctly in __init__."""
    assert windows_bash_session._initialized
    assert windows_bash_session.work_dir == os.path.abspath(temp_work_dir)
    # initialize() method is now trivial, just confirms readiness
    assert windows_bash_session.initialize() is True


def test_command_execution(windows_bash_session):
    """Test basic command execution."""
    # Test a simple command
    action = CmdRunAction(command='Write-Output "Hello World"')
    result = windows_bash_session.execute(action)

    assert isinstance(result, CmdOutputObservation)
    # Check content, stripping potential trailing newlines
    content = result.content.strip()
    assert content == "Hello World"
    assert result.exit_code == 0

    # Test a simple command with a newline
    action = CmdRunAction(command='Write-Output "Hello\\n World"')
    result = windows_bash_session.execute(action)

    assert isinstance(result, CmdOutputObservation)
    # Check content, stripping potential trailing newlines
    content = result.content.strip()
    assert content == "Hello\\n World"
    assert result.exit_code == 0


def test_command_with_error(windows_bash_session):
    """Test command execution with an error reported via Write-Error."""
    # Test a command that will write an error
    action = CmdRunAction(command="Write-Error 'Test Error'")
    result = windows_bash_session.execute(action)

    assert isinstance(result, CmdOutputObservation)
    # Error stream is captured and appended
    assert "Failed" in result.content
    # Our implementation should set exit code to 1 when errors occur in stream
    assert result.exit_code == 1


def test_command_failure_exit_code(windows_bash_session):
    """Test command execution that results in a non-zero exit code."""
    # Test a command that causes a script failure (e.g., invalid cmdlet)
    action = CmdRunAction(command="Get-NonExistentCmdlet")
    result = windows_bash_session.execute(action)

    assert isinstance(result, CmdOutputObservation)
    # Error should be captured in the output
    assert "Failed" in result.content
    assert "is not recognized" in result.content or "CommandNotFoundException" in result.content
    assert result.exit_code == 1


def test_control_commands(windows_bash_session):
    """Test handling of control commands (not supported)."""
    # Test Ctrl+C - should return ErrorObservation if no command is running
    action_c = CmdRunAction(command="C-c", is_input=True)
    result_c = windows_bash_session.execute(action_c)
    assert isinstance(result_c, ErrorObservation)
    assert "No active process to interrupt" in result_c.content # Updated expected message

    # Test unsupported control command
    action_d = CmdRunAction(command="C-d", is_input=True)
    result_d = windows_bash_session.execute(action_d)
    assert isinstance(result_d, ErrorObservation)
    assert "not supported" in result_d.content


def test_command_timeout(windows_bash_session):
    """Test command timeout handling."""
    # Test a command that will timeout
    test_timeout_sec = 1
    action = CmdRunAction(command=f"Start-Sleep -Seconds 5")
    action.set_hard_timeout(test_timeout_sec)
    start_time = time.monotonic()
    result = windows_bash_session.execute(action)
    duration = time.monotonic() - start_time

    assert isinstance(result, CmdOutputObservation)
    # Check for timeout specific metadata
    assert "timed out" in result.metadata.suffix.lower() # Check suffix, not content
    assert result.exit_code == -1  # Timeout should result in exit code -1
    # Check that it actually timed out near the specified time
    assert abs(duration - test_timeout_sec) < 0.5  # Allow some buffer


def test_long_running_command(windows_bash_session):
    action = CmdRunAction(command='python -u -m http.server 8081')
    action.set_hard_timeout(1)
    result = windows_bash_session.execute(action)

    assert isinstance(result, CmdOutputObservation)
    # Verify the initial output was captured
    assert 'Serving HTTP on' in result.content
    # Check for timeout specific metadata
    assert (
        "[The command timed out after 1 seconds. You may wait longer to see additional output by sending empty command '', send other commands to interact with the current process, or send keys to interrupt/kill the command.]"
        in result.metadata.suffix
    )
    assert result.exit_code == -1

    # The action timed out, but the command should be still running
    # We should now be able to interrupt it
    action = CmdRunAction(command='C-c', is_input=True)
    action.set_hard_timeout(30) # Give it enough time to stop
    result = windows_bash_session.execute(action)

    assert isinstance(result, CmdOutputObservation)
    # On Windows, Stop-Job termination doesn't inherently return output.
    # The CmdOutputObservation will have content="" and exit_code=0 if successful.
    # The KeyboardInterrupt message assertion is removed as it's added manually
    # by the wrapper and might not be guaranteed depending on timing/implementation details.
    assert result.exit_code == 0
    # Assert that the "Keyboard interrupt received" message is present, as it's now manually added.
    assert 'Keyboard interrupt received, exiting.' in result.content

    # Verify the server is actually stopped by starting another one on the same port
    action = CmdRunAction(command='python -u -m http.server 8081')
    action.set_hard_timeout(1) # Set a short timeout to check if it starts
    result = windows_bash_session.execute(action)

    assert isinstance(result, CmdOutputObservation)
    # Verify the initial output was captured, indicating the port was free
    assert 'Serving HTTP on' in result.content
    # The command will time out again, so the exit code should be -1
    assert result.exit_code == -1

    # Clean up the second server process
    action = CmdRunAction(command='C-c', is_input=True)
    action.set_hard_timeout(30)
    result = windows_bash_session.execute(action)
    assert result.exit_code == 0


def test_multiple_commands(windows_bash_session):
    """Test executing multiple commands in sequence."""
    # Test multiple independent commands
    action1 = CmdRunAction(command="Write-Output 'First'")
    result1 = windows_bash_session.execute(action1)
    assert isinstance(result1, CmdOutputObservation)
    assert result1.content.strip() == "First"
    assert result1.exit_code == 0

    action2 = CmdRunAction(command="Write-Output 'Second'")
    result2 = windows_bash_session.execute(action2)
    assert isinstance(result2, CmdOutputObservation)
    assert result2.content.strip() == "Second"
    assert result2.exit_code == 0

    # Test variable persistence - runspace should maintain variable state
    action_set_var = CmdRunAction(command="$MyVar = 'Temp'; Write-Output $MyVar")
    result_set_var = windows_bash_session.execute(action_set_var)
    assert isinstance(result_set_var, CmdOutputObservation)
    assert result_set_var.content.strip() == "Temp"
    assert result_set_var.exit_code == 0

    action_use_var = CmdRunAction(command="Write-Output $MyVar")
    result_use_var = windows_bash_session.execute(action_use_var)
    assert isinstance(result_use_var, CmdOutputObservation)
    # $MyVar should still exist in the persistent runspace
    assert result_use_var.content.strip() == "Temp"
    assert result_use_var.exit_code == 0


def test_multiple_commands_rejected_and_individual_execution(windows_bash_session):
    """Test that executing multiple commands separated by newline is rejected,
    but individual commands (including multiline) execute correctly."""
    # Define a list of commands, including multiline and special characters
    cmds = [
            'Get-ChildItem',
            'Write-Output "hello`nworld"',
            """Write-Output "hello it's me\"""",
            """Write-Output `
    'hello' `
    -NoNewline""",
            """Write-Output 'hello`nworld`nare`nyou`nthere?'""",
            """Write-Output 'hello`nworld`nare`nyou`n`nthere?'""",
            """Write-Output 'hello`nworld `"'""",  # Escape the trailing double quote
        ]
    joined_cmds = "\n".join(cmds)

    # 1. Test that executing multiple commands at once fails
    action_multi = CmdRunAction(command=joined_cmds)
    result_multi = windows_bash_session.execute(action_multi)

    assert isinstance(result_multi, ErrorObservation)
    assert "ERROR: Cannot execute multiple commands at once" in result_multi.content

    # 2. Now run each command individually and verify they work
    results = []
    for cmd in cmds:
        action_single = CmdRunAction(command=cmd)
        obs = windows_bash_session.execute(action_single)
        assert isinstance(obs, CmdOutputObservation)
        assert obs.exit_code == 0
        results.append(obs.content.strip()) # Strip trailing newlines for comparison


def test_working_directory(windows_bash_session, temp_work_dir):
    """Test working directory handling."""
    initial_cwd = windows_bash_session._cwd
    abs_temp_work_dir = os.path.abspath(temp_work_dir)
    assert initial_cwd == abs_temp_work_dir

    # Create a subdirectory
    sub_dir_path = Path(abs_temp_work_dir) / "subdir"
    sub_dir_path.mkdir()
    assert sub_dir_path.is_dir()
    sub_dir_str = str(sub_dir_path)

    # Test changing directory
    action_cd = CmdRunAction(command=f"Set-Location '{sub_dir_str}'")
    result_cd = windows_bash_session.execute(action_cd)
    assert isinstance(result_cd, CmdOutputObservation)
    assert result_cd.exit_code == 0
    # Check that the session's internal CWD state was updated
    assert windows_bash_session._cwd == sub_dir_str
    # Check that the metadata reflects the directory *after* the command
    assert result_cd.metadata.working_dir == sub_dir_str

    # Execute a command in the new directory to confirm
    action_pwd = CmdRunAction(command="(Get-Location).Path")
    result_pwd = windows_bash_session.execute(action_pwd)
    assert isinstance(result_pwd, CmdOutputObservation)
    assert result_pwd.exit_code == 0
    # Check the command output reflects the new directory
    assert result_pwd.content.strip() == sub_dir_str
    # Metadata should also reflect the current directory
    assert result_pwd.metadata.working_dir == sub_dir_str

    # Test changing back to original directory
    action_cd_back = CmdRunAction(command=f"Set-Location '{abs_temp_work_dir}'")
    result_cd_back = windows_bash_session.execute(action_cd_back)
    assert isinstance(result_cd_back, CmdOutputObservation)
    assert result_cd_back.exit_code == 0
    assert windows_bash_session._cwd == abs_temp_work_dir
    assert result_cd_back.metadata.working_dir == abs_temp_work_dir


def test_cleanup(windows_bash_session):
    """Test proper cleanup of resources (runspace)."""
    # Session should be initialized before close
    assert windows_bash_session._initialized
    assert windows_bash_session.runspace is not None

    # Close the session
    windows_bash_session.close()

    # Verify cleanup
    assert not windows_bash_session._initialized
    assert windows_bash_session.runspace is None
    assert windows_bash_session._closed


def test_syntax_error_handling(windows_bash_session):
    """Test handling of syntax errors in PowerShell commands."""
    # Test invalid command syntax
    action = CmdRunAction(command="Write-Output 'Missing Quote")
    result = windows_bash_session.execute(action)
    assert isinstance(result, CmdOutputObservation)
    # Error message appears in the output via PowerShell error stream
    assert "missing" in result.content.lower() or "terminator" in result.content.lower()
    assert result.exit_code == 1


def test_special_characters_handling(windows_bash_session):
    """Test handling of commands containing special characters."""
    # Test command with special characters
    special_chars_cmd = '''Write-Output "Special Chars: \`& \`| \`< \`> \`\` \`' \`\" \`! \`$ \`% \`^ \`( \`) \`- \`= \`+ \`[ \`] \`{ \`} \`; \`: \`, \`. \`? \`/ \`~"'''
    action = CmdRunAction(command=special_chars_cmd)
    result = windows_bash_session.execute(action)
    assert isinstance(result, CmdOutputObservation)
    # Check output contains the special characters
    assert "Special Chars:" in result.content
    assert "&" in result.content and "|" in result.content
    assert result.exit_code == 0


def test_empty_command(windows_bash_session):
    """Test handling of empty command string when no command is running."""
    action = CmdRunAction(command="")
    result = windows_bash_session.execute(action)
    assert isinstance(result, CmdOutputObservation)
    # Should indicate error as per test_bash.py behavior
    assert "ERROR: No previous running command to retrieve logs from." in result.content
    # Exit code is typically 0 even for this specific "error" message in the bash implementation
    assert result.exit_code == 0


def test_exception_during_execution(windows_bash_session):
    """Test handling of exceptions during command execution."""
    # Patch the PowerShell class itself within the module where it's used
    patch_target = 'openhands.runtime.utils.windows_bash.PowerShell'

    # Create a mock PowerShell class
    mock_powershell_class = MagicMock()
    # Configure its Create method (which is called in execute) to raise an exception
    # This simulates an error during the creation of the PowerShell object itself.
    mock_powershell_class.Create.side_effect = Exception("Test exception from mocked Create")

    with patch(patch_target, mock_powershell_class):
        action = CmdRunAction(command="Write-Output 'Test'")
        # Now, when execute calls PowerShell.Create(), it will hit our mock and raise the exception
        result = windows_bash_session.execute(action)

        # The exception should be caught by the try...except block in execute()
        assert isinstance(result, ErrorObservation)
        # Check the error message generated by the execute method's exception handler
        assert "FATAL ERROR executing PowerShell command" in result.content
        assert "Test exception from mocked Create" in result.content


def test_streaming_output(windows_bash_session):
    """Test handling of streaming output from commands."""
    # Command that produces output incrementally
    command = """
    1..3 | ForEach-Object {
        Write-Output "Line $_"
        Start-Sleep -Milliseconds 100
    }
    """
    action = CmdRunAction(command=command)
    result = windows_bash_session.execute(action)
    
    assert isinstance(result, CmdOutputObservation)
    assert "Line 1" in result.content
    assert "Line 2" in result.content
    assert "Line 3" in result.content
    assert result.exit_code == 0


def test_shutdown_signal_handling(windows_bash_session):
    """Test handling of shutdown signal during command execution."""
    # This would require mocking the shutdown_listener, which might be complex.
    # For now, we'll just verify that a long-running command can be executed
    # and that execute() returns properly.
    command = "Start-Sleep -Seconds 1"
    action = CmdRunAction(command=command)
    result = windows_bash_session.execute(action)
    
    assert isinstance(result, CmdOutputObservation)
    assert result.exit_code == 0


def test_runspace_state_after_error(windows_bash_session):
    """Test that the runspace remains usable after a command error."""
    # First, execute a command with an error
    error_action = CmdRunAction(command="NonExistentCommand")
    error_result = windows_bash_session.execute(error_action)
    assert isinstance(error_result, CmdOutputObservation)
    assert error_result.exit_code == 1
    
    # Then, execute a valid command
    valid_action = CmdRunAction(command="Write-Output 'Still working'")
    valid_result = windows_bash_session.execute(valid_action)
    assert isinstance(valid_result, CmdOutputObservation)
    assert "Still working" in valid_result.content
    assert valid_result.exit_code == 0


def test_stateful_file_operations(windows_bash_session, temp_work_dir):
    """Test file operations to verify runspace state persistence.
    
    This test verifies that:
    1. The working directory state persists between commands
    2. File operations work correctly relative to the current directory
    3. The runspace maintains state for path-dependent operations
    """
    abs_temp_work_dir = os.path.abspath(temp_work_dir)
    
    # 1. Create a subdirectory
    sub_dir_name = "file_test_dir"
    sub_dir_path = Path(abs_temp_work_dir) / sub_dir_name
    
    # Use PowerShell to create directory
    create_dir_action = CmdRunAction(command=f"New-Item -Path '{sub_dir_name}' -ItemType Directory")
    result = windows_bash_session.execute(create_dir_action)
    assert result.exit_code == 0
    
    # Verify directory exists on disk
    assert sub_dir_path.exists() and sub_dir_path.is_dir()
    
    # 2. Change to the new directory
    cd_action = CmdRunAction(command=f"Set-Location '{sub_dir_name}'")
    result = windows_bash_session.execute(cd_action)
    assert result.exit_code == 0
    assert windows_bash_session._cwd == str(sub_dir_path)
    
    # 3. Create a file in the current directory (which should be the subdirectory)
    test_content = "This is a test file created by PowerShell"
    create_file_action = CmdRunAction(
        command=f"Set-Content -Path 'test_file.txt' -Value '{test_content}'"
    )
    result = windows_bash_session.execute(create_file_action)
    assert result.exit_code == 0
    
    # 4. Verify file exists at the expected path (in the subdirectory)
    expected_file_path = sub_dir_path / "test_file.txt"
    assert expected_file_path.exists() and expected_file_path.is_file()
    
    # 5. Read file contents using PowerShell and verify
    read_file_action = CmdRunAction(command="Get-Content -Path 'test_file.txt'")
    result = windows_bash_session.execute(read_file_action)
    assert result.exit_code == 0
    assert test_content in result.content
    
    # 6. Go back to parent and try to access file using relative path
    cd_parent_action = CmdRunAction(command="Set-Location ..")
    result = windows_bash_session.execute(cd_parent_action)
    assert result.exit_code == 0
    assert windows_bash_session._cwd == abs_temp_work_dir
    
    # 7. Read the file using relative path
    read_from_parent_action = CmdRunAction(
        command=f"Get-Content -Path '{sub_dir_name}/test_file.txt'"
    )
    result = windows_bash_session.execute(read_from_parent_action)
    assert result.exit_code == 0
    assert test_content in result.content
    
    # 8. Clean up
    remove_file_action = CmdRunAction(
        command=f"Remove-Item -Path '{sub_dir_name}/test_file.txt' -Force"
    )
    result = windows_bash_session.execute(remove_file_action)
    assert result.exit_code == 0

# Add tests similar to test_bash.py for command output continuation

def test_command_output_continuation(windows_bash_session):
    """Test retrieving continued output using empty command after timeout."""
    # Start a command that produces output slowly
    action = CmdRunAction('1..5 | ForEach-Object { Write-Output $_; Start-Sleep 2 }') # Sleep 2s per line
    action.set_hard_timeout(1.5) # Timeout after 1.5s
    obs = windows_bash_session.execute(action)
    assert isinstance(obs, CmdOutputObservation)
    assert obs.content.strip() == '1' # Should only see the first line
    assert obs.metadata.prefix == ''
    assert '[The command timed out after 1.5 seconds.' in obs.metadata.suffix
    assert obs.exit_code == -1 # Still running

    # Continue watching output with empty command
    action = CmdRunAction('')
    action.set_hard_timeout(1.5) # Another timeout
    obs = windows_bash_session.execute(action)
    assert isinstance(obs, CmdOutputObservation)
    assert '[Below is the output of the previous command.]' in obs.metadata.prefix
    assert obs.content.strip() == '' # Should see no new output within 1.5s
    assert '[The command timed out after 1.5 seconds.' in obs.metadata.suffix
    assert obs.exit_code == -1 # Still running

    # Continue again
    action = CmdRunAction('')
    action.set_hard_timeout(1.5) # Another timeout
    obs = windows_bash_session.execute(action)
    assert isinstance(obs, CmdOutputObservation)
    assert '[Below is the output of the previous command.]' in obs.metadata.prefix
    assert obs.content.strip() == '2' # Should see the second line now
    assert '[The command timed out after 1.5 seconds.' in obs.metadata.suffix
    assert obs.exit_code == -1 # Still running

    # Continue until completion
    for expected in ['3', '4', '5']:
        action = CmdRunAction('')
        action.set_hard_timeout(3) # Give enough time for next output
        obs = windows_bash_session.execute(action)
        assert isinstance(obs, CmdOutputObservation)
        assert (
            '[Below is the output of the previous command.]' in obs.metadata.prefix
        )
        assert obs.content.strip() == expected
        if expected == '5':
             # The command should complete after printing '5'
             assert '[The command completed with exit code 0.]' in obs.metadata.suffix
             assert obs.exit_code == 0
        else:
             # Still running if not the last line
             assert '[The command timed out after 3 seconds.' in obs.metadata.suffix
             assert obs.exit_code == -1

    # Final empty command should confirm completion (or show error if it failed)
    action = CmdRunAction('')
    obs = windows_bash_session.execute(action)
    assert isinstance(obs, CmdOutputObservation)
    assert '[The command completed with exit code 0.]' in obs.metadata.suffix
    assert obs.exit_code == 0

def test_long_running_command_followed_by_execute(windows_bash_session):
    """Tests behavior when a new command is sent while another is running after timeout."""
    # Start a slow command
    action = CmdRunAction('1..3 | ForEach-Object { Write-Output $_; Start-Sleep 3 }')
    action.set_hard_timeout(2.5)
    obs = windows_bash_session.execute(action)
    assert isinstance(obs, CmdOutputObservation)
    assert '1' in obs.content
    assert obs.exit_code == -1
    assert '[The command timed out after 2.5 seconds.' in obs.metadata.suffix
    assert obs.metadata.prefix == ''

    # Send another command while the first is still running in the background
    action = CmdRunAction('Write-Output "New Command"')
    obs = windows_bash_session.execute(action)
    assert isinstance(obs, CmdOutputObservation)
    assert '[Below is the output of the previous command.]' in obs.metadata.prefix
    # The new command should not execute, and we should get an error message in the suffix
    assert 'New Command' not in obs.content # The new command output shouldn't be here
    # Should contain output from the *original* command ('2') if it arrived
    assert '2' in obs.content or obs.content == '' # Content might be '2' or empty depending on timing
    assert 'Your command "Write-Output "New Command"" is NOT executed.' in obs.metadata.suffix
    assert 'The previous command is still running' in obs.metadata.suffix
    assert obs.exit_code == -1 # Still running the *original* command

    # Send an empty command to get the next output from the original command
    action = CmdRunAction('')
    action.set_hard_timeout(4) # Enough time for '3'
    obs = windows_bash_session.execute(action)
    assert isinstance(obs, CmdOutputObservation)
    assert '[Below is the output of the previous command.]' in obs.metadata.prefix
    # Should contain '3' if the original command finished
    if '2' in obs.content: # If '2' was already printed in the previous step
        assert '3' in obs.content
    else: # If '2' wasn't printed previously, it might be here along with '3' or just '3'
         assert '2' in obs.content or '3' in obs.content
    assert '[The command completed with exit code 0.]' in obs.metadata.suffix
    assert obs.exit_code == 0 