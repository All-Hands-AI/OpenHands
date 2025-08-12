from openhands.runtime.utils.bash import split_bash_commands


def test_comment_followed_by_command():
    """Test that a comment followed by a command is correctly handled as multiple commands."""
    input_command = """# Let me just check the current git status and push directly
git status --porcelain"""

    # Current behavior - this will return two commands
    result = split_bash_commands(input_command)

    # This test should fail with the current implementation
    # but will pass after our fix
    assert len(result) == 1, f'Expected 1 command, got {len(result)}: {result}'
    assert 'git status --porcelain' in result[0]


def test_multiple_comments_followed_by_command():
    """Test that multiple comments followed by a command are correctly handled as a single command."""
    input_command = """# First comment
# Second comment
# Third comment
git status"""

    # Current behavior - this will return multiple commands
    result = split_bash_commands(input_command)

    # This test should fail with the current implementation
    # but will pass after our fix
    assert len(result) == 1, f'Expected 1 command, got {len(result)}: {result}'
    assert 'git status' in result[0]


def test_comment_only():
    """Test that a comment-only input is handled as a single command."""
    input_command = """# This is just a comment
# Another comment line"""

    # Current behavior - this will return multiple commands
    result = split_bash_commands(input_command)

    # This test should fail with the current implementation
    # but will pass after our fix
    assert len(result) == 1, f'Expected 1 command, got {len(result)}: {result}'
