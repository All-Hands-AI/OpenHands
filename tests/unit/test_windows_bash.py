import os
import pytest
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch
import time
import subprocess

from openhands.runtime.utils.windows_bash import WindowsBashSession 
from openhands.events.action import CmdRunAction
from openhands.events.observation.commands import CmdOutputObservation, CmdOutputMetadata
from openhands.events.observation import ErrorObservation


@pytest.fixture
def temp_work_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
def windows_bash_session(temp_work_dir):
    """Create a WindowsBashSession instance for testing."""
    # Instantiate the new class
    session = WindowsBashSession(
        work_dir=temp_work_dir,
        username=None, 
        # no_change_timeout_seconds is not relevant here
    )
    yield session
    session.close()


def test_initialization(windows_bash_session, temp_work_dir):
    """Test that the session initializes correctly."""
    assert not windows_bash_session._initialized
    windows_bash_session.initialize()
    assert windows_bash_session._initialized
    assert windows_bash_session.work_dir == temp_work_dir
    assert windows_bash_session._process is not None
    # Ensure the process is actually running
    assert windows_bash_session._process.poll() is None


def test_command_execution(windows_bash_session):
    """Test basic command execution."""
    windows_bash_session.initialize()
    
    # Test a simple command
    action = CmdRunAction(command="Write-Output 'Hello World'")
    result = windows_bash_session.execute(action)
    
    assert isinstance(result, CmdOutputObservation)
    # Check content, stripping potential BOM and trailing newlines from file read
    assert result.content.strip().lstrip('\ufeff') == "Hello World"
    assert result.metadata.exit_code == 0


def test_command_with_error(windows_bash_session):
    """Test command execution with an error reported via Write-Error."""
    windows_bash_session.initialize()
    
    # Test a command that will write an error but still exit 0 (default PS behavior)
    action = CmdRunAction(command="Write-Error 'Test Error'")
    result = windows_bash_session.execute(action)
    
    assert isinstance(result, CmdOutputObservation)
    assert "Test Error" in result.content 
    # Write-Error doesn't necessarily change $LASTEXITCODE unless used with -ErrorAction Stop
    # The error message itself appears in the output stream (stderr redirected to stdout in script)
    assert result.metadata.exit_code == 0 # Default exit code is 0 unless script explicitly sets it

def test_command_failure_exit_code(windows_bash_session):
    """Test command execution that results in a non-zero exit code."""
    windows_bash_session.initialize()

    # Test a command that causes a script failure (e.g., invalid cmdlet)
    action = CmdRunAction(command="Get-NonExistentCmdlet")
    result = windows_bash_session.execute(action)

    assert isinstance(result, CmdOutputObservation)
    assert "Get-NonExistentCmdlet" in result.content # Error message should be captured
    assert "not recognized" in result.content 
    assert result.metadata.exit_code == 1 # Script wrapper should set exit code to 1 on catch


def test_special_keys(windows_bash_session):
    """Test handling of special keys (Ctrl+C)."""
    windows_bash_session.initialize()
    
    # Test Ctrl+C
    action = CmdRunAction(command="C-c")
    result = windows_bash_session.execute(action)
    
    assert isinstance(result, CmdOutputObservation)
    # Check the specific content returned for C-c
    assert "Interrupt signal (Ctrl+C)" in result.content
    assert result.metadata.exit_code == 130 # Standard exit code for SIGINT

    # Test unsupported key
    action_unsupported = CmdRunAction(command="C-d")
    result_unsupported = windows_bash_session.execute(action_unsupported)
    assert isinstance(result_unsupported, ErrorObservation)
    assert "not supported" in result_unsupported.content


def test_command_timeout(windows_bash_session):
    """Test command timeout handling."""
    windows_bash_session.initialize()
    
    # Test a command that will timeout by checking the exit code file
    test_timeout_sec = 1
    action = CmdRunAction(command=f"Start-Sleep -Seconds 5", timeout=test_timeout_sec)
    result = windows_bash_session.execute(action)
    
    assert isinstance(result, CmdOutputObservation)
    # Check for timeout specific content and metadata
    assert f"timed out after {test_timeout_sec} seconds" in result.content
    assert result.metadata.exit_code == 124 # Standard timeout exit code
    assert f"timed out after {test_timeout_sec} seconds" in result.metadata.suffix

# Removed test_no_change_timeout as it's not applicable to this implementation
# def test_no_change_timeout(windows_bash_session):
#     ...

def test_multiple_commands(windows_bash_session):
    """Test executing multiple commands in sequence."""
    windows_bash_session.initialize()
    
    # Test multiple commands
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

    action3 = CmdRunAction(command="$MyVar = 'Third'; Write-Output $MyVar")
    result3 = windows_bash_session.execute(action3)
    assert isinstance(result3, CmdOutputObservation)
    assert result3.content.strip().lstrip('\ufeff') == "Third"
    assert result3.metadata.exit_code == 0


def test_working_directory(windows_bash_session, temp_work_dir):
    """Test working directory handling."""
    windows_bash_session.initialize()
    initial_cwd = windows_bash_session._cwd
    assert initial_cwd == temp_work_dir
    
    # Create a subdirectory
    sub_dir = Path(temp_work_dir) / "subdir"
    sub_dir.mkdir()
    assert sub_dir.is_dir()

    # Test changing directory
    action_cd = CmdRunAction(command=f"Set-Location '{sub_dir}'")
    result_cd = windows_bash_session.execute(action_cd)
    assert isinstance(result_cd, CmdOutputObservation)
    assert result_cd.metadata.exit_code == 0
    # Verify the internal cwd was updated (based on stdout marker)
    assert windows_bash_session._cwd == str(sub_dir)

    # Execute a command in the new directory
    action_pwd = CmdRunAction(command="(Get-Location).Path")
    result_pwd = windows_bash_session.execute(action_pwd)
    assert isinstance(result_pwd, CmdOutputObservation)
    assert result_pwd.metadata.exit_code == 0
    # Check the command output reflects the new directory
    assert result_pwd.content.strip().lstrip('\ufeff') == str(sub_dir)
    assert result_pwd.metadata.working_dir == str(sub_dir)


def test_cleanup(windows_bash_session):
    """Test proper cleanup of resources."""
    windows_bash_session.initialize()
    temp_dir_path = windows_bash_session._temp_dir # Store path before close
    
    # Verify process is running and temp dir exists
    assert windows_bash_session._process is not None
    assert windows_bash_session._process.poll() is None
    assert temp_dir_path.is_dir()
    
    # Close the session
    windows_bash_session.close()
    
    # Verify cleanup
    assert windows_bash_session._process is None
    assert not windows_bash_session._initialized
    # Check temp dir is removed
    assert not temp_dir_path.exists() 


def test_error_handling(windows_bash_session):
    """Test error handling in various scenarios."""
    windows_bash_session.initialize()
    
    # Test invalid command syntax (should be caught by PowerShell)
    action = CmdRunAction(command="Write-Output 'Missing Quote")
    result = windows_bash_session.execute(action)
    assert isinstance(result, CmdOutputObservation)
    assert "missing closing quote" in result.content.lower()
    assert result.metadata.exit_code == 1 # Wrapper catches exception, sets exit code to 1
    
    # Test command with special characters
    action_var = CmdRunAction(command='$TestVar = "Special&"; Write-Output "Var is $TestVar"')
    result_var = windows_bash_session.execute(action_var)
    assert isinstance(result_var, CmdOutputObservation)
    assert "Var is Special&" in result_var.content
    assert result_var.metadata.exit_code == 0


def test_session_reuse(windows_bash_session):
    """Test that the session can be reused after closing and re-initializing."""
    # Initialize, use, and close
    windows_bash_session.initialize()
    action1 = CmdRunAction(command="Write-Output 'First Use'")
    result1 = windows_bash_session.execute(action1)
    assert isinstance(result1, CmdOutputObservation)
    assert "First Use" in result1.content
    windows_bash_session.close()
    assert not windows_bash_session._initialized
    assert windows_bash_session._process is None
    
    # Try to re-initialize and reuse the same session object
    windows_bash_session.initialize()
    assert windows_bash_session._initialized
    assert windows_bash_session._process is not None
    action2 = CmdRunAction(command="Write-Output 'Reused Session'")
    result2 = windows_bash_session.execute(action2)
    
    assert isinstance(result2, CmdOutputObservation)
    assert "Reused Session" in result2.content.strip().lstrip('\ufeff')
    assert result2.metadata.exit_code == 0


def test_command_output_handling(windows_bash_session):
    """Test handling of command output and metadata, including setting exit code."""
    windows_bash_session.initialize()
    
    # Test command that explicitly sets $LASTEXITCODE
    action = CmdRunAction(command="Write-Output 'Test Output'; $global:LASTEXITCODE = 42")
    result = windows_bash_session.execute(action)
    
    assert isinstance(result, CmdOutputObservation)
    assert "Test Output" in result.content
    assert result.metadata.exit_code == 42


def test_initialization_failure():
    """Test handling of initialization failures when Popen fails."""
    with patch('subprocess.Popen') as mock_popen:
        # Simulate Popen raising an exception
        mock_popen.side_effect = OSError("Failed to start process")
        
        session = WindowsBashSession(work_dir="test_dir")
        
        with pytest.raises(RuntimeError) as exc_info:
            session.initialize()
        
        assert "Failed to start PowerShell" in str(exc_info.value)
        assert "Failed to start process" in str(exc_info.value)

def test_initialization_process_dies():
    """Test handling of initialization failures when the process dies immediately."""
    with patch('subprocess.Popen') as mock_popen:
        # Simulate process starting but dying immediately
        mock_process = MagicMock()
        mock_process.poll.return_value = 1 # Indicate process has exited
        mock_process.pid = 1234
        mock_popen.return_value = mock_process
        
        session = WindowsBashSession(work_dir="test_dir")
        
        with pytest.raises(RuntimeError) as exc_info:
            session.initialize()
        
        assert "PowerShell process terminated" in str(exc_info.value)
        assert "code 1" in str(exc_info.value) 