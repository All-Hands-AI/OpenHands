import pytest
from unittest.mock import patch

from openhands.runtime.utils.bash import split_bash_commands


def is_comment_only(command: str) -> bool:
    """Check if a command consists only of comments."""
    lines = command.strip().split('\n')
    return all(line.strip().startswith('#') for line in lines if line.strip())


def test_comment_followed_by_command():
    """Test that a comment followed by a command is correctly handled as multiple commands."""
    input_command = """# Let me just check the current git status and push directly
    git status --porcelain"""

    # Split the command into multiple commands
    result = split_bash_commands(input_command)
    
    # Verify that we get multiple commands (this is the current behavior)
    assert len(result) == 2
    
    # Verify that the first command is a comment
    assert is_comment_only(result[0])
    
    # Verify that the second command is not a comment
    assert not is_comment_only(result[1])


def test_multiple_comments_followed_by_command():
    """Test that multiple comments followed by a command are correctly handled as a single command."""
    input_command = """# First comment
    # Second comment
    # Third comment
    git status"""

    # Split the command into multiple commands
    result = split_bash_commands(input_command)
    
    # Verify that we get multiple commands (this is the current behavior)
    assert len(result) == 2
    
    # Verify that the first command is a comment
    assert is_comment_only(result[0])
    
    # Verify that the second command is not a comment
    assert not is_comment_only(result[1])


def test_comment_only():
    """Test that a comment-only input is handled as a single command."""
    input_command = """# This is just a comment
# Another comment line"""

    # Split the command into multiple commands
    result = split_bash_commands(input_command)
    
    # Verify that we get a single command (this is the current behavior)
    assert len(result) == 1
    
    # Verify that the command is a comment
    assert is_comment_only(result[0])


def test_is_comment_only_function():
    """Test the is_comment_only function."""
    # Test with a single comment
    assert is_comment_only("# This is a comment")
    
    # Test with multiple comments
    assert is_comment_only("# First comment\n# Second comment")
    
    # Test with a command
    assert not is_comment_only("git status")
    
    # Test with a comment followed by a command
    assert not is_comment_only("# Comment\ngit status")
    
    # Test with a command followed by a comment
    assert not is_comment_only("git status\n# Comment")