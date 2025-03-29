import os
import pytest
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from openhands.runtime.utils.windows_bash import WindowsBashSession
from openhands.events.action import CmdRunAction
from openhands.events.observation.commands import CmdOutputObservation, CmdOutputMetadata


@pytest.fixture
def temp_work_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
def windows_bash_session(temp_work_dir):
    """Create a WindowsBashSession instance for testing."""
    session = WindowsBashSession(
        work_dir=temp_work_dir,
        username=None,
        no_change_timeout_seconds=1,
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


def test_command_execution(windows_bash_session):
    """Test basic command execution."""
    windows_bash_session.initialize()
    
    # Test a simple command
    action = CmdRunAction(command="Write-Output 'Hello World'")
    result = windows_bash_session.execute(action)
    
    assert isinstance(result, CmdOutputObservation)
    assert "Hello World" in result.content
    assert result.metadata.exit_code == 0


def test_command_with_error(windows_bash_session):
    """Test command execution with an error."""
    windows_bash_session.initialize()
    
    # Test a command that will fail
    action = CmdRunAction(command="Write-Error 'Test Error'")
    result = windows_bash_session.execute(action)
    
    assert isinstance(result, CmdOutputObservation)
    assert "Test Error" in result.content
    assert result.metadata.exit_code == 1


def test_special_keys(windows_bash_session):
    """Test handling of special keys (Ctrl+C, etc)."""
    windows_bash_session.initialize()
    
    # Test Ctrl+C
    action = CmdRunAction(command="C-c")
    result = windows_bash_session.execute(action)
    
    assert isinstance(result, CmdOutputObservation)
    assert "CTRL+C was sent" in result.metadata.suffix


def test_command_timeout(windows_bash_session):
    """Test command timeout handling."""
    windows_bash_session.initialize()
    
    # Test a command that will timeout
    action = CmdRunAction(command="Start-Sleep -Seconds 10")
    action.set_hard_timeout(1)  # Set 1 second timeout
    result = windows_bash_session.execute(action)
    
    assert isinstance(result, CmdOutputObservation)
    assert "timed out after 1 seconds" in result.metadata.suffix


def test_no_change_timeout(windows_bash_session):
    """Test no-change timeout handling."""
    windows_bash_session.initialize()
    
    # Test a command that produces no output
    action = CmdRunAction(command="Start-Sleep -Seconds 5")
    action.blocking = False  # Make it non-blocking
    result = windows_bash_session.execute(action)
    
    assert isinstance(result, CmdOutputObservation)
    assert "has no new output after 1 seconds" in result.metadata.suffix


def test_multiple_commands(windows_bash_session):
    """Test executing multiple commands in sequence."""
    windows_bash_session.initialize()
    
    # Test multiple commands
    commands = [
        "Write-Output 'First'",
        "Write-Output 'Second'",
        "Write-Output 'Third'"
    ]
    
    for cmd in commands:
        action = CmdRunAction(command=cmd)
        result = windows_bash_session.execute(action)
        assert isinstance(result, CmdOutputObservation)
        assert result.metadata.exit_code == 0


def test_working_directory(windows_bash_session, temp_work_dir):
    """Test working directory handling."""
    windows_bash_session.initialize()
    
    # Test changing directory
    action = CmdRunAction(command=f"Set-Location '{temp_work_dir}'")
    result = windows_bash_session.execute(action)
    assert isinstance(result, CmdOutputObservation)
    assert result.metadata.exit_code == 0
    
    # Verify the working directory was updated
    assert windows_bash_session.cwd == temp_work_dir


def test_cleanup(windows_bash_session):
    """Test proper cleanup of resources."""
    windows_bash_session.initialize()
    
    # Verify process is running
    assert windows_bash_session._process is not None
    assert windows_bash_session._process.poll() is None
    
    # Close the session
    windows_bash_session.close()
    
    # Verify cleanup
    assert windows_bash_session._process is None
    assert windows_bash_session._closed


def test_error_handling(windows_bash_session):
    """Test error handling in various scenarios."""
    windows_bash_session.initialize()
    
    # Test invalid command
    action = CmdRunAction(command="Invalid-Command")
    result = windows_bash_session.execute(action)
    assert isinstance(result, CmdOutputObservation)
    assert result.metadata.exit_code == 1
    
    # Test command with special characters
    action = CmdRunAction(command='Write-Output "Test $var"')
    result = windows_bash_session.execute(action)
    assert isinstance(result, CmdOutputObservation)
    assert result.metadata.exit_code == 0


def test_session_reuse(windows_bash_session):
    """Test that the session can be reused after closing."""
    windows_bash_session.initialize()
    windows_bash_session.close()
    
    # Try to reuse the session
    windows_bash_session.initialize()
    action = CmdRunAction(command="Write-Output 'Reused Session'")
    result = windows_bash_session.execute(action)
    
    assert isinstance(result, CmdOutputObservation)
    assert "Reused Session" in result.content
    assert result.metadata.exit_code == 0


def test_command_output_handling(windows_bash_session):
    """Test handling of command output and metadata."""
    windows_bash_session.initialize()
    
    # Test command with output and metadata
    action = CmdRunAction(command="Write-Output 'Test Output'; $LASTEXITCODE = 42")
    result = windows_bash_session.execute(action)
    
    assert isinstance(result, CmdOutputObservation)
    assert "Test Output" in result.content
    assert result.metadata.exit_code == 42


def test_initialization_failure():
    """Test handling of initialization failures."""
    with patch('subprocess.Popen') as mock_popen:
        # Simulate process failure
        mock_process = MagicMock()
        mock_process.poll.return_value = 1
        mock_process.stderr.read.return_value = "Initialization Error"
        mock_popen.return_value = mock_process
        
        session = WindowsBashSession(work_dir="test_dir")
        
        with pytest.raises(RuntimeError) as exc_info:
            session.initialize()
        
        assert "PowerShell process failed to start" in str(exc_info.value) 