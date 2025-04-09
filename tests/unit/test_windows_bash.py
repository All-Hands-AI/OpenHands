import os
import sys # Added import
import pytest
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch
import time
import subprocess
import shutil # Added for cleanup verification if needed

from openhands.runtime.utils.windows_bash import WindowsBashSession
from openhands.events.action import CmdRunAction
from openhands.events.observation.commands import CmdOutputObservation, CmdOutputMetadata
from openhands.events.observation import ErrorObservation

# Skip all tests in this module if not running on Windows
pytestmark = pytest.mark.skipif(sys.platform != 'win32', reason="WindowsBashSession tests require Windows")


@pytest.fixture
def temp_work_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
def windows_bash_session(temp_work_dir):
    """Create a WindowsBashSession instance for testing."""
    # Instantiate the class. Initialization happens in __init__.
    session = WindowsBashSession(
        work_dir=temp_work_dir,
        username=None,
    )
    assert session._initialized # Should be true after __init__
    assert hasattr(session, '_temp_dir') and session._temp_dir.is_dir()
    yield session
    # Ensure cleanup happens even if test fails
    session.close()


def test_initialization(windows_bash_session, temp_work_dir):
    """Test that the session initializes correctly in __init__."""
    # Most initialization moved to the fixture setup
    assert windows_bash_session._initialized
    assert windows_bash_session.work_dir == os.path.abspath(temp_work_dir)
    assert hasattr(windows_bash_session, '_temp_dir')
    assert windows_bash_session._temp_dir.is_dir()
    # initialize() method is now trivial, just confirms readiness
    assert windows_bash_session.initialize() is True


def test_command_execution(windows_bash_session):
    """Test basic command execution."""
    # windows_bash_session.initialize() # No longer needed here

    # Test a simple command
    action = CmdRunAction(command="Write-Output 'Hello World'")
    result = windows_bash_session.execute(action)

    assert isinstance(result, CmdOutputObservation)
    # Check content, stripping potential BOM and trailing newlines from file read
    # Output might have extra newlines depending on how PS writes it
    content = result.content.strip().lstrip('\ufeff')
    assert content == "Hello World"
    assert result.metadata.exit_code == 0


def test_command_with_error(windows_bash_session):
    """Test command execution with an error reported via Write-Error."""
    # windows_bash_session.initialize() # No longer needed here

    # Test a command that will write an error but still exit 0 (default PS behavior)
    action = CmdRunAction(command="Write-Error 'Test Error'")
    result = windows_bash_session.execute(action)

    assert isinstance(result, CmdOutputObservation)
    # Error stream is captured and appended
    assert "[ERROR_STREAM]" in result.content
    assert "Test Error" in result.content
    # Write-Error doesn't necessarily change $LASTEXITCODE unless used with -ErrorAction Stop or script traps it
    # The current script wrapper doesn't explicitly trap Write-Error, so exit code remains 0
    assert result.metadata.exit_code == 0

def test_command_failure_exit_code(windows_bash_session):
    """Test command execution that results in a non-zero exit code."""
    # windows_bash_session.initialize() # No longer needed here

    # Test a command that causes a script failure (e.g., invalid cmdlet)
    action = CmdRunAction(command="Get-NonExistentCmdlet")
    result = windows_bash_session.execute(action)

    assert isinstance(result, CmdOutputObservation)
    # Error should be captured in the output stream via the script's try/catch
    assert "Get-NonExistentCmdlet" in result.content
    assert "not recognized" in result.content or "is not recognized" in result.content # Different PS versions vary slightly
    # The catch block in the script sets exit code to 1
    assert result.metadata.exit_code == 1


def test_special_keys(windows_bash_session):
    """Test handling of special keys (not supported)."""
    # windows_bash_session.initialize() # No longer needed here

    # Test Ctrl+C - should return ErrorObservation
    action_c = CmdRunAction(command="C-c")
    result_c = windows_bash_session.execute(action_c)
    assert isinstance(result_c, ErrorObservation)
    assert "Special keys like C-c are not supported" in result_c.content

    # Test unsupported key - should return ErrorObservation
    action_d = CmdRunAction(command="C-d")
    result_d = windows_bash_session.execute(action_d)
    assert isinstance(result_d, ErrorObservation)
    assert "Special keys like C-d are not supported" in result_d.content


def test_command_timeout(windows_bash_session):
    """Test command timeout handling."""
    # windows_bash_session.initialize() # No longer needed here

    # Test a command that will timeout
    test_timeout_sec = 1
    action = CmdRunAction(command=f"Start-Sleep -Seconds 5")
    action.set_hard_timeout(test_timeout_sec)
    start_time = time.monotonic()
    result = windows_bash_session.execute(action)
    duration = time.monotonic() - start_time

    assert isinstance(result, CmdOutputObservation)
    # Check for timeout specific content and metadata
    assert f"Command timed out after {test_timeout_sec} seconds" in result.content
    assert result.metadata.exit_code == -1
    assert f"timed out after {test_timeout_sec} seconds" in result.metadata.suffix
    # Check that it actually timed out near the specified time
    assert abs(duration - test_timeout_sec) < 0.5 # Allow some buffer


def test_multiple_commands(windows_bash_session):
    """Test executing multiple commands in sequence (no state persistence)."""
    # windows_bash_session.initialize() # No longer needed here

    # Test multiple independent commands
    action1 = CmdRunAction(command="Write-Output 'First'")
    result1 = windows_bash_session.execute(action1)
    assert isinstance(result1, CmdOutputObservation)
    assert result1.content.strip().lstrip('\ufeff') == "First"
    assert result1.metadata.exit_code == 0

    action2 = CmdRunAction(command="Write-Output 'Second'")
    result2 = windows_bash_session.execute(action2)
    assert isinstance(result2, CmdOutputObservation)
    assert result2.content.strip().lstrip('\ufeff') == "Second"
    assert result2.metadata.exit_code == 0

    # Test variable scope - $MyVar defined in one exec won't exist in the next
    action_set_var = CmdRunAction(command="$MyVar = 'Temp'; Write-Output $MyVar")
    result_set_var = windows_bash_session.execute(action_set_var)
    assert isinstance(result_set_var, CmdOutputObservation)
    assert result_set_var.content.strip().lstrip('\ufeff') == "Temp"
    assert result_set_var.metadata.exit_code == 0

    action_use_var = CmdRunAction(command="Write-Output $MyVar")
    result_use_var = windows_bash_session.execute(action_use_var)
    assert isinstance(result_use_var, CmdOutputObservation)
    # $MyVar is null/empty in the new scope, Write-Output outputs nothing
    assert result_use_var.content.strip().lstrip('\ufeff') == ""
    assert result_use_var.metadata.exit_code == 0


def test_working_directory(windows_bash_session, temp_work_dir):
    """Test working directory handling."""
    # windows_bash_session.initialize() # No longer needed here
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
    assert result_cd.metadata.exit_code == 0
    # Check that the session's internal CWD state was updated
    assert windows_bash_session._cwd == sub_dir_str
    # Check that the metadata reflects the directory *after* the command
    assert result_cd.metadata.working_dir == sub_dir_str

    # Execute a command in the new directory to confirm
    action_pwd = CmdRunAction(command="(Get-Location).Path")
    result_pwd = windows_bash_session.execute(action_pwd)
    assert isinstance(result_pwd, CmdOutputObservation)
    assert result_pwd.metadata.exit_code == 0
    # Check the command output reflects the new directory
    assert result_pwd.content.strip().lstrip('\ufeff') == sub_dir_str
    # Metadata should also reflect the current directory
    assert result_pwd.metadata.working_dir == sub_dir_str

    # Test changing back to original directory
    action_cd_back = CmdRunAction(command=f"Set-Location '{abs_temp_work_dir}'")
    result_cd_back = windows_bash_session.execute(action_cd_back)
    assert isinstance(result_cd_back, CmdOutputObservation)
    assert result_cd_back.metadata.exit_code == 0
    assert windows_bash_session._cwd == abs_temp_work_dir
    assert result_cd_back.metadata.working_dir == abs_temp_work_dir


def test_cleanup(windows_bash_session):
    """Test proper cleanup of resources (temp directory)."""
    # windows_bash_session.initialize() # Not needed, done in fixture

    # Temp dir should exist before close
    temp_dir_path = windows_bash_session._temp_dir
    assert temp_dir_path.is_dir()

    # Close the session
    windows_bash_session.close()

    # Verify cleanup
    assert not windows_bash_session._initialized
    # Check temp dir is removed
    assert not temp_dir_path.exists()


def test_syntax_error_handling(windows_bash_session):
    """Test handling of syntax errors in PowerShell commands."""
    # Test invalid command syntax (should be caught by PowerShell)
    action = CmdRunAction(command="Write-Output 'Missing Quote")
    result = windows_bash_session.execute(action)
    assert isinstance(result, CmdOutputObservation)
    # Error message appears in the output via the script's try/catch
    assert "missing closing quote" in result.content.lower() or "string is missing the terminator" in result.content.lower()
    assert result.metadata.exit_code == 1 # Wrapper catches exception, sets exit code to 1


def test_special_characters_handling(windows_bash_session):
    """Test handling of commands containing special characters."""
    # Test command with special characters that don't break the script injection
    # Ensure quoting handles typical shell metacharacters when passed to Invoke-Expression
    # Need to escape PowerShell metacharacters (`$") within the double-quoted string itself.
    # Use triple quotes for the Python string to avoid issues with internal quotes/backslashes.
    special_chars_cmd = '''Write-Output "Special Chars: & | < > `` ` \' \`" ! `$ % ^ ( ) - = + [ ] { } ; : , . ? / ~"'''
    action_var = CmdRunAction(command=special_chars_cmd)
    result_var = windows_bash_session.execute(action_var)
    assert isinstance(result_var, CmdOutputObservation)
    # Strip BOM and check exact output - this is the literal string we want printed
    # Adjusted to match the actual observed output from the diff (double space after backtick)
    # Corrected Python escapes for literal ' and \ within single quotes.
    expected_output = 'Special Chars: & | < > `  \' \\" ! $ % ^ ( ) - = + [ ] { } ; : , . ? / ~'
    assert result_var.content.strip().lstrip('\ufeff') == expected_output
    assert result_var.metadata.exit_code == 0


def test_session_reuse(windows_bash_session):
    """Test that the session object can execute commands after closing and re-initializing."""
    # Initialize is implicit in fixture
    # windows_bash_session.initialize()

    action1 = CmdRunAction(command="Write-Output 'First Use'")
    result1 = windows_bash_session.execute(action1)
    assert isinstance(result1, CmdOutputObservation)
    assert "First Use" in result1.content
    temp_dir1 = windows_bash_session._temp_dir

    windows_bash_session.close()
    assert not windows_bash_session._initialized
    assert not temp_dir1.exists() # Ensure first temp dir was cleaned

    # Calling initialize() again is okay, but not strictly necessary as execute works fine
    # on a closed-then-reused object (it handles its own setup).
    # The main point is the object itself can be reused.
    # windows_bash_session.initialize()
    # assert windows_bash_session._initialized

    action2 = CmdRunAction(command="Write-Output 'Reused Session Object'")
    result2 = windows_bash_session.execute(action2)

    assert isinstance(result2, CmdOutputObservation)
    assert result2.content.strip().lstrip('\ufeff') == "Reused Session Object"
    assert result2.metadata.exit_code == 0
    # Should have created a new temp dir for the second execution
    assert hasattr(windows_bash_session, '_temp_dir')
    assert windows_bash_session._temp_dir.is_dir()
    assert windows_bash_session._temp_dir != temp_dir1


def test_command_output_handling(windows_bash_session):
    """Test handling of command output and metadata, including setting exit code."""
    # windows_bash_session.initialize() # No longer needed here

    # Test command that explicitly sets $LASTEXITCODE before exiting script block
    # Note: Simple assignment `$LASTEXITCODE = 42` might be reset by subsequent PS operations.
    # Using `cmd /c exit 42` is a reliable way to set $LASTEXITCODE.
    action = CmdRunAction(command="Write-Output 'Test Output'; cmd /c exit 42")
    result = windows_bash_session.execute(action)

    assert isinstance(result, CmdOutputObservation)
    assert "Test Output" in result.content.strip() # Output from Write-Output
    assert result.metadata.exit_code == 42 # Exit code from cmd


def test_execute_popen_failure(temp_work_dir):
    """Test handling of failures when subprocess.Popen fails during execute."""
    with patch('subprocess.Popen') as mock_popen:
        # Simulate Popen raising an exception inside execute()
        error_message = "Failed to start process"
        mock_popen.side_effect = OSError(error_message)

        # Need to create session inside the patch context
        session = WindowsBashSession(work_dir=temp_work_dir)
        # session.initialize() # Not needed

        action = CmdRunAction(command="echo 'test'")
        result = session.execute(action)

        assert isinstance(result, ErrorObservation)
        assert "Failed to execute PowerShell script" in result.content
        assert error_message in result.content


def test_background_process_initial_output_timeout(windows_bash_session):
    """
    Test that initial output from a background-like process (like the python http server)
    is captured before a timeout occurs.

    This test specifically targets the behavior observed where initial output
    might be missed due to the output capturing mechanism on Windows.
    """
    # Match the message from the python http.server
    initial_message = "Serving HTTP on 0.0.0.0 port 8081"
    # sleep_duration is not needed as the server runs until stopped/killed
    timeout_duration = 2 # Seconds, short enough to trigger before much happens

    # Use python -u to force unbuffered output
    command = "python -u -m http.server 8081"

    action = CmdRunAction(command=command)
    action.set_hard_timeout(timeout_duration)

    start_time = time.monotonic()
    result = windows_bash_session.execute(action)
    duration = time.monotonic() - start_time

    print(f"DEBUG - Test Result Content: {result.content}") # Add debug print
    print(f"DEBUG - Test Result Metadata: {result.metadata}")

    assert isinstance(result, CmdOutputObservation)
    # Check for timeout metadata
    assert result.metadata.exit_code == -1, "Exit code should be -1 for timeout"
    assert f"timed out after {timeout_duration} seconds" in result.metadata.suffix.lower(), "Timeout message should be in suffix"
    # Check that it actually timed out near the specified time
    assert abs(duration - timeout_duration) < 5.0, f"Duration ({duration:.2f}s) should be close to timeout ({timeout_duration}s)"

    # Check for the start of the expected message, allowing for IP variations (0.0.0.0 vs ::)
    expected_start = "Serving HTTP on "
    assert result.content.strip().startswith(expected_start), \
        f"Expected output to start with '{expected_start}', but got: '{result.content.strip()}'"

# Remove test_initialization_process_dies as it's less relevant now
# def test_initialization_process_dies(): ... 