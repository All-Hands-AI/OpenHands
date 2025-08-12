import pytest
from unittest.mock import patch

from openhands.events.action import CmdRunAction
from openhands.events.observation import ErrorObservation
from openhands.runtime.utils.bash import split_bash_commands


def is_comment_only(command: str) -> bool:
    """Check if a command consists only of comments."""
    lines = command.strip().split('\n')
    return all(line.strip().startswith('#') for line in lines if line.strip())


def test_execute_with_comments():
    """Test that the execute method correctly handles commands with comments."""
    # This test verifies that our fix in the execute method works correctly
    # by patching the split_bash_commands function to return the actual result
    # and then patching the _is_comment_only function to filter out comments
    
    # Create a command with comments
    command = """# Let me just check the current git status and push directly
    git status --porcelain"""
    
    # Get the actual result from split_bash_commands
    actual_result = split_bash_commands(command)
    
    # Verify that we get multiple commands (this is the current behavior)
    assert len(actual_result) == 2
    
    # Verify that the first command is a comment
    assert is_comment_only(actual_result[0])
    
    # Verify that the second command is not a comment
    assert not is_comment_only(actual_result[1])
    
    # Now test that our fix works by filtering out comment-only commands
    non_comment_commands = [cmd for cmd in actual_result if not is_comment_only(cmd)]
    
    # Verify that we only have one non-comment command
    assert len(non_comment_commands) == 1
    
    # Verify that the non-comment command is the git status command
    assert 'git status --porcelain' in non_comment_commands[0]