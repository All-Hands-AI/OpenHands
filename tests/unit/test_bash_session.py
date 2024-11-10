import pytest
import time
from openhands.runtime.utils.bash import BashSession

def test_basic_command():
    session = BashSession()
    
    # Test simple command
    result = session.execute("echo 'hello world'")
    assert "hello world" in result.content
    assert result.exit_code == 0
    
    # Test command with error
    result = session.execute("nonexistent_command")
    assert result.exit_code != 0
    assert "command not found" in result.content.lower()

def test_long_running_command():
    session = BashSession()
    
    # Start a long-running command
    result = session.execute("sleep 2 && echo 'done sleeping'")
    assert "done sleeping" in result.content
    assert result.exit_code == 0
    
    # Test timeout behavior
    result = session.execute("sleep 5", timeout=1)
    assert "screen is still changing now" in result.content
    assert result.exit_code == -1  # Indicates command is still running

def test_interactive_command():
    session = BashSession()
    
    # Test interactive command
    result = session.execute("read -p 'Enter name: ' name && echo \"Hello $name\"")
    assert "Enter name:" in result.content
    assert result.exit_code == -1  # Indicates waiting for input
    
    # Send input
    result = session.execute("John")
    assert "Hello John" in result.content
    assert result.exit_code == 0

def test_ctrl_c():
    session = BashSession()
    
    # Start infinite loop
    result = session.execute("while true; do echo 'looping'; sleep 1; done")
    assert "looping" in result.content
    assert result.exit_code == -1
    
    # Send Ctrl+C
    result = session.execute("ctrl+c")
    assert result.exit_code == 130  # Standard exit code for Ctrl+C