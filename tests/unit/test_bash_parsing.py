import pytest

from openhands.runtime.utils.bash import escape_bash_special_chars, split_bash_commands


def test_split_commands_util():
    cmds = [
        'ls -l',
        'echo -e "hello\nworld"',
        """
echo -e "hello it\\'s me"
""".strip(),
        """
echo \\
    -e 'hello' \\
    -v
""".strip(),
        """
echo -e 'hello\\nworld\\nare\\nyou\\nthere?'
""".strip(),
        """
echo -e 'hello
world
are
you\\n
there?'
""".strip(),
        """
echo -e 'hello
world "
'
""".strip(),
        """
kubectl apply -f - <<EOF
apiVersion: v1
kind: Pod
metadata:
  name: busybox-sleep
spec:
  containers:
  - name: busybox
    image: busybox:1.28
    args:
    - sleep
    - "1000000"
EOF
""".strip(),
        """
mkdir -p _modules && \
for month in {01..04}; do
    for day in {01..05}; do
        touch "_modules/2024-${month}-${day}-sample.md"
    done
done
""".strip(),
    ]
    joined_cmds = '\n'.join(cmds)
    split_cmds = split_bash_commands(joined_cmds)
    for s in split_cmds:
        print('\nCMD')
        print(s)
    for i in range(len(cmds)):
        assert (
            split_cmds[i].strip() == cmds[i].strip()
        ), f'At index {i}: {split_cmds[i]} != {cmds[i]}.'


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
    expected_output = [
        'echo "Hello" # This is a comment\n# This is another comment',
        'ls -l',
    ]
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
        # it will fall back to return the original input
        assert split_bash_commands(input_command) == [input_command]


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
    expected_output = [
        'echo "Hello" # This is a comment\n# This is another comment',
        'ls -l',
    ]
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
        # it will fall back to return the original input
        assert split_bash_commands(input_command) == [input_command]


def test_escape_bash_special_chars():
    test_cases = [
        # Basic cases - use raw strings (r'') to avoid Python escape sequence warnings
        ('echo test \\; ls', 'echo test \\\\; ls'),
        ('grep pattern \\| sort', 'grep pattern \\\\| sort'),
        ('cmd1 \\&\\& cmd2', 'cmd1 \\\\&\\\\& cmd2'),
        ('cat file \\> output.txt', 'cat file \\\\> output.txt'),
        ('cat \\< input.txt', 'cat \\\\< input.txt'),
        # Quoted strings should remain unchanged
        ('echo "test \\; unchanged"', 'echo "test \\; unchanged"'),
        ("echo 'test \\| unchanged'", "echo 'test \\| unchanged'"),
        # Mixed quoted and unquoted
        (
            'echo "quoted \\;" \\; "more" \\| grep',
            'echo "quoted \\;" \\\\; "more" \\\\| grep',
        ),
        # Multiple escapes in sequence
        ('cmd1 \\;\\|\\& cmd2', 'cmd1 \\\\;\\\\|\\\\& cmd2'),
        # Commands with other backslashes
        ('echo test\\ntest', 'echo test\\ntest'),
        ('echo "test\\ntest"', 'echo "test\\ntest"'),
        # Edge cases
        ('', ''),  # Empty string
        ('\\\\', '\\\\'),  # Double backslash
        ('\\"', '\\"'),  # Escaped quote
    ]

    for input_cmd, expected in test_cases:
        result = escape_bash_special_chars(input_cmd)
        assert (
            result == expected
        ), f'Failed on input "{input_cmd}"\nExpected: "{expected}"\nGot: "{result}"'


def test_escape_bash_special_chars_with_invalid_syntax():
    invalid_inputs = [
        'echo "unclosed quote',
        "echo 'unclosed quote",
        'cat <<EOF\nunclosed heredoc',
    ]
    for input_cmd in invalid_inputs:
        # Should return original input when parsing fails
        result = escape_bash_special_chars(input_cmd)
        assert result == input_cmd, f'Failed to handle invalid input: {input_cmd}'


def test_escape_bash_special_chars_with_heredoc():
    input_cmd = r"""cat <<EOF
line1 \; not escaped
line2 \| not escaped
EOF"""
    # Heredoc content should not be escaped
    expected = input_cmd
    result = escape_bash_special_chars(input_cmd)
    assert (
        result == expected
    ), f'Failed to handle heredoc correctly\nExpected: {expected}\nGot: {result}'


def test_escape_bash_special_chars_with_parameter_expansion():
    test_cases = [
        # Parameter expansion should be preserved
        ('echo $HOME', 'echo $HOME'),
        ('echo ${HOME}', 'echo ${HOME}'),
        ('echo ${HOME:-default}', 'echo ${HOME:-default}'),
        # Mixed with special chars
        ('echo $HOME \\; ls', 'echo $HOME \\\\; ls'),
        ('echo ${PATH} \\| grep bin', 'echo ${PATH} \\\\| grep bin'),
        # Quoted parameter expansion
        ('echo "$HOME"', 'echo "$HOME"'),
        ('echo "${HOME}"', 'echo "${HOME}"'),
        # Complex parameter expansions
        ('echo ${var:=default} \\; ls', 'echo ${var:=default} \\\\; ls'),
        ('echo ${!prefix*} \\| sort', 'echo ${!prefix*} \\\\| sort'),
    ]

    for input_cmd, expected in test_cases:
        result = escape_bash_special_chars(input_cmd)
        assert (
            result == expected
        ), f'Failed on input "{input_cmd}"\nExpected: "{expected}"\nGot: "{result}"'


def test_escape_bash_special_chars_with_command_substitution():
    test_cases = [
        # Basic command substitution
        ('echo $(pwd)', 'echo $(pwd)'),
        ('echo `pwd`', 'echo `pwd`'),
        # Mixed with special chars
        ('echo $(pwd) \\; ls', 'echo $(pwd) \\\\; ls'),
        ('echo `pwd` \\| grep home', 'echo `pwd` \\\\| grep home'),
        # Nested command substitution
        ('echo $(echo `pwd`)', 'echo $(echo `pwd`)'),
        # Complex command substitution
        ('echo $(find . -name "*.txt" \\; ls)', 'echo $(find . -name "*.txt" \\; ls)'),
        # Mixed with quotes
        ('echo "$(pwd)"', 'echo "$(pwd)"'),
        ('echo "`pwd`"', 'echo "`pwd`"'),
    ]

    for input_cmd, expected in test_cases:
        result = escape_bash_special_chars(input_cmd)
        assert (
            result == expected
        ), f'Failed on input "{input_cmd}"\nExpected: "{expected}"\nGot: "{result}"'


def test_escape_bash_special_chars_mixed_nodes():
    test_cases = [
        # Mix of parameter expansion and command substitution
        ('echo $HOME/$(pwd)', 'echo $HOME/$(pwd)'),
        # Mix with special chars
        ('echo $HOME/$(pwd) \\; ls', 'echo $HOME/$(pwd) \\\\; ls'),
        # Complex mixed cases
        (
            'echo "${HOME}/$(basename `pwd`) \\; next"',
            'echo "${HOME}/$(basename `pwd`) \\; next"',
        ),
        (
            'VAR=${HOME} \\; echo $(pwd)',
            'VAR=${HOME} \\\\; echo $(pwd)',
        ),
        # Real-world examples
        (
            'find . -name "*.txt" -exec grep "${PATTERN:-default}" {} \\;',
            'find . -name "*.txt" -exec grep "${PATTERN:-default}" {} \\\\;',
        ),
        (
            'echo "Current path: ${PWD}/$(basename `pwd`)" \\| grep home',
            'echo "Current path: ${PWD}/$(basename `pwd`)" \\\\| grep home',
        ),
    ]

    for input_cmd, expected in test_cases:
        result = escape_bash_special_chars(input_cmd)
        assert (
            result == expected
        ), f'Failed on input "{input_cmd}"\nExpected: "{expected}"\nGot: "{result}"'


def test_escape_bash_special_chars_with_chained_commands():
    test_cases = [
        # Basic chained commands
        ('ls && pwd', 'ls && pwd'),
        ('echo "hello" && ls', 'echo "hello" && ls'),
        # Chained commands with special chars
        ('ls \\; pwd && echo test', 'ls \\\\; pwd && echo test'),
        ('echo test && grep pattern \\| sort', 'echo test && grep pattern \\\\| sort'),
        # Complex chained cases
        ('echo ${HOME} && ls \\; pwd', 'echo ${HOME} && ls \\\\; pwd'),
        (
            'echo "$(pwd)" && cat file \\> out.txt',
            'echo "$(pwd)" && cat file \\\\> out.txt',
        ),
        # Multiple chains
        ('cmd1 && cmd2 && cmd3', 'cmd1 && cmd2 && cmd3'),
        (
            'cmd1 \\; ls && cmd2 \\| grep && cmd3',
            'cmd1 \\\\; ls && cmd2 \\\\| grep && cmd3',
        ),
    ]

    for input_cmd, expected in test_cases:
        result = escape_bash_special_chars(input_cmd)
        assert (
            result == expected
        ), f'Failed on input "{input_cmd}"\nExpected: "{expected}"\nGot: "{result}"'
