import pytest

from opendevin.runtime.utils.bash_command_splitter import split_bash_commands


@pytest.mark.parametrize(
    'input_command, expected_output',
    [
        ('ls -l', ['ls -l']),
        ("echo 'Hello, world!'", ["echo 'Hello, world!'"]),
        ('cd /tmp && touch test.txt', ['cd /tmp && touch test.txt']),
        ("echo -e 'line1\\nline2\\nline3'", ["echo -e 'line1\\nline2\\nline3'"]),
        (
            "grep 'pattern' file.txt | sort | uniq",
            ["grep 'pattern' file.txt | sort | uniq"],
        ),
        ('for i in {1..5}; do echo $i; done', ['for i in {1..5}; do echo $i; done']),
        (
            "echo 'Single quotes don\\'t escape'",
            ["echo 'Single quotes don\\'t escape'"],
        ),
        (
            'echo "Double quotes \\"do\\" escape"',
            ['echo "Double quotes \\"do\\" escape"'],
        ),
    ],
)
def test_single_commands(input_command, expected_output):
    assert split_bash_commands(input_command) == expected_output


@pytest.mark.parametrize(
    'input_commands, expected_output',
    [
        ("ls -l; echo 'Hello'; cd /tmp", ['ls -l', "echo 'Hello'", 'cd /tmp']),
        (
            'echo \'one; two\'; echo "three; four"',
            ["echo 'one; two'", 'echo "three; four"'],
        ),
        ('echo one\\; two; echo three', ['echo one\\; two', 'echo three']),
    ],
)
def test_multiple_commands(input_commands, expected_output):
    assert split_bash_commands(input_commands) == expected_output


def test_heredoc():
    input_commands = """
cat <<EOF
multiline
text
EOF
echo "Done"
"""
    expected_output = ['cat <<EOF\nmultiline\ntext\nEOF', 'echo "Done"']
    assert split_bash_commands(input_commands) == expected_output


def test_backslash_continuation():
    input_commands = """
echo "This is a long \
command that spans \
multiple lines"
echo "Next command"
"""
    expected_output = [
        'echo "This is a long command that spans multiple lines"',
        'echo "Next command"',
    ]
    assert split_bash_commands(input_commands) == expected_output


def test_comments():
    input_commands = """
echo "Hello" # This is a comment
# This is another comment
ls -l
"""
    expected_output = ['echo "Hello"', 'ls -l']
    assert split_bash_commands(input_commands) == expected_output


def test_complex_quoting():
    input_commands = """
echo "This is a \\"quoted\\" string"
echo 'This is a '\''single-quoted'\'' string'
echo "Mixed 'quotes' in \\"double quotes\\""
"""
    expected_output = [
        'echo "This is a \\"quoted\\" string"',
        "echo 'This is a '''single-quoted''' string'",
        'echo "Mixed \'quotes\' in \\"double quotes\\""',
    ]
    assert split_bash_commands(input_commands) == expected_output


def test_invalid_syntax():
    invalid_inputs = [
        'echo "Unclosed quote',
        "echo 'Unclosed quote",
        'cat <<EOF\nUnclosed heredoc',
    ]
    for input_command in invalid_inputs:
        with pytest.raises(ValueError):
            split_bash_commands(input_command)


@pytest.fixture
def sample_commands():
    return [
        'ls -l',
        'echo "Hello, world!"',
        'cd /tmp && touch test.txt',
        'echo -e "line1\\nline2\\nline3"',
        'grep "pattern" file.txt | sort | uniq',
        'for i in {1..5}; do echo $i; done',
        'cat <<EOF\nmultiline\ntext\nEOF',
        'echo "Escaped \\"quotes\\""',
        "echo 'Single quotes don\\'t escape'",
        'echo "Command with a trailing backslash \\\n  and continuation"',
    ]


def test_split_single_commands(sample_commands):
    for cmd in sample_commands:
        result = split_bash_commands(cmd)
        assert len(result) == 1, f'Expected single command, got: {result}'


def test_split_multiple_commands():
    input_commands = "ls -l; echo 'Hello'; cd /tmp"
    expected_output = ['ls -l', "echo 'Hello'", 'cd /tmp']
    result = split_bash_commands(input_commands)
    assert result == expected_output, f'Expected {expected_output}, got {result}'


def test_split_commands_with_semicolons_in_quotes():
    input_commands = 'echo \'one; two\'; echo "three; four"'
    expected_output = ["echo 'one; two'", 'echo "three; four"']
    result = split_bash_commands(input_commands)
    assert result == expected_output, f'Expected {expected_output}, got {result}'


def test_split_commands_with_escaped_semicolons():
    input_commands = 'echo one\\; two; echo three'
    expected_output = ['echo one\\; two', 'echo three']
    result = split_bash_commands(input_commands)
    assert result == expected_output, f'Expected {expected_output}, got {result}'


def test_split_commands_with_heredoc():
    input_commands = """
cat <<EOF
multiline
text
EOF
echo "Done"
"""
    expected_output = ['cat <<EOF\nmultiline\ntext\nEOF', 'echo "Done"']
    result = split_bash_commands(input_commands)
    assert result == expected_output, f'Expected {expected_output}, got {result}'


def test_split_commands_with_backslash_continuation():
    input_commands = """
echo "This is a long \
command that spans \
multiple lines"
echo "Next command"
"""
    expected_output = [
        'echo "This is a long command that spans multiple lines"',
        'echo "Next command"',
    ]
    result = split_bash_commands(input_commands)
    assert result == expected_output, f'Expected {expected_output}, got {result}'


def test_split_commands_with_empty_lines():
    input_commands = """
ls -l

echo "Hello"

cd /tmp
"""
    expected_output = ['ls -l', 'echo "Hello"', 'cd /tmp']
    result = split_bash_commands(input_commands)
    assert result == expected_output, f'Expected {expected_output}, got {result}'


def test_split_commands_with_comments():
    input_commands = """
echo "Hello" # This is a comment
# This is another comment
ls -l
"""
    expected_output = ['echo "Hello"', 'ls -l']
    result = split_bash_commands(input_commands)
    assert result == expected_output, f'Expected {expected_output}, got {result}'


def test_split_commands_with_complex_quoting():
    input_commands = """
echo "This is a \\"quoted\\" string"
echo "Mixed 'quotes' in \\"double quotes\\""
"""
    # echo 'This is a '\''single-quoted'\'' string'

    expected_output = [
        'echo "This is a \\"quoted\\" string"',
        'echo "Mixed \'quotes\' in \\"double quotes\\""',
    ]
    # "echo 'This is a '\\''single-quoted'\\'' string'",
    result = split_bash_commands(input_commands)
    assert result == expected_output, f'Expected {expected_output}, got {result}'


def test_split_commands_with_invalid_input():
    invalid_inputs = [
        'echo "Unclosed quote',
        "echo 'Unclosed quote",
        'cat <<EOF\nUnclosed heredoc',
    ]
    for input_command in invalid_inputs:
        with pytest.raises(ValueError):
            split_bash_commands(input_command)
