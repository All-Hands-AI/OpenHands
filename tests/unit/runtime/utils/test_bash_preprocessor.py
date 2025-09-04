"""Tests for bash command preprocessor."""

import sys
from pathlib import Path

# Add the module path directly to avoid full OpenHands import chain
test_dir = Path(__file__).parent
utils_dir = test_dir.parent.parent.parent.parent / 'openhands' / 'runtime' / 'utils'
sys.path.insert(0, str(utils_dir))

# ruff: noqa: E402
from bash_preprocessor import BashCommandPreprocessor


class TestBashCommandPreprocessor:
    """Test cases for BashCommandPreprocessor."""

    def setup_method(self):
        """Set up test fixtures."""
        self.preprocessor = BashCommandPreprocessor()

    def test_is_problematic_command_basic_cases(self):
        """Test detection of basic problematic commands."""
        # Problematic commands
        assert self.preprocessor.is_problematic_command('set -e')
        assert self.preprocessor.is_problematic_command('set -u')
        assert self.preprocessor.is_problematic_command('set -eu')
        assert self.preprocessor.is_problematic_command('set -euo pipefail')
        assert self.preprocessor.is_problematic_command('set -o errexit')
        assert self.preprocessor.is_problematic_command('set -o nounset')
        assert self.preprocessor.is_problematic_command('set -o pipefail')
        assert self.preprocessor.is_problematic_command('set --errexit')
        assert self.preprocessor.is_problematic_command('set --nounset')
        assert self.preprocessor.is_problematic_command('set --pipefail')

        # Safe commands
        assert not self.preprocessor.is_problematic_command('echo hello')
        assert not self.preprocessor.is_problematic_command('set -x')
        assert not self.preprocessor.is_problematic_command('set -v')
        assert not self.preprocessor.is_problematic_command('set +e')
        assert not self.preprocessor.is_problematic_command('unset variable')
        assert not self.preprocessor.is_problematic_command('')
        assert not self.preprocessor.is_problematic_command('   ')

    def test_is_problematic_command_with_chaining(self):
        """Test detection of problematic commands with chaining."""
        # Commands with && chaining
        assert self.preprocessor.is_problematic_command('set -e && echo hello')
        assert self.preprocessor.is_problematic_command(
            'set -euo pipefail && non-existent-command'
        )
        assert self.preprocessor.is_problematic_command('set -o errexit && ls')

        # Commands with ; chaining
        assert self.preprocessor.is_problematic_command('set -e; echo hello')
        assert self.preprocessor.is_problematic_command(
            'set -euo pipefail; non-existent-command'
        )

        # Commands at end of line
        assert self.preprocessor.is_problematic_command('echo start && set -e')
        assert self.preprocessor.is_problematic_command('ls; set -euo pipefail')

    def test_is_problematic_command_case_insensitive(self):
        """Test that detection is case insensitive."""
        assert self.preprocessor.is_problematic_command('SET -E')
        assert self.preprocessor.is_problematic_command('Set -Eu')
        assert self.preprocessor.is_problematic_command('set -O ERREXIT')
        assert self.preprocessor.is_problematic_command('SET --ERREXIT')

    def test_extract_set_commands(self):
        """Test extraction of set commands from complex strings."""
        # Single set command
        commands = self.preprocessor.extract_set_commands('set -e')
        assert 'set -e' in commands

        # Multiple set commands
        commands = self.preprocessor.extract_set_commands('set -e && set -o pipefail')
        assert len(commands) == 2
        assert any('set -e' in cmd for cmd in commands)
        assert any('pipefail' in cmd for cmd in commands)

        # Set command in middle of other commands
        commands = self.preprocessor.extract_set_commands(
            'echo start && set -euo pipefail && echo end'
        )
        assert len(commands) == 1
        assert 'set -euo pipefail' in commands[0]

        # No set commands
        commands = self.preprocessor.extract_set_commands('echo hello && ls -la')
        assert len(commands) == 0

    def test_transform_command_basic(self):
        """Test basic command transformation."""
        # Problematic command should be wrapped
        transformed, was_transformed = self.preprocessor.transform_command('set -e')
        assert was_transformed
        assert transformed == '( set -e )'

        # Safe command should not be transformed
        transformed, was_transformed = self.preprocessor.transform_command('echo hello')
        assert not was_transformed
        assert transformed == 'echo hello'

        # Empty command should not be transformed
        transformed, was_transformed = self.preprocessor.transform_command('')
        assert not was_transformed
        assert transformed == ''

    def test_transform_command_complex(self):
        """Test transformation of complex commands."""
        # Command with chaining
        original = 'set -euo pipefail && non-existent-command'
        transformed, was_transformed = self.preprocessor.transform_command(original)
        assert was_transformed
        assert transformed == f'( {original} )'

        # Command with multiple parts
        original = 'echo start && set -e && echo end'
        transformed, was_transformed = self.preprocessor.transform_command(original)
        assert was_transformed
        assert transformed == f'( {original} )'

    def test_transform_command_preserves_functionality(self):
        """Test that transformation preserves the intended functionality."""
        # The original problematic case from the issue
        original = 'set -euo pipefail && non-existant-command'
        transformed, was_transformed = self.preprocessor.transform_command(original)

        assert was_transformed
        assert transformed == f'( {original} )'

        # Verify the transformation makes sense
        # The subshell should contain the original command
        assert original in transformed
        assert transformed.startswith('(')
        assert transformed.endswith(')')

    def test_get_warning_message(self):
        """Test generation of warning messages."""
        original = 'set -euo pipefail && non-existent-command'
        transformed = '( set -euo pipefail && non-existent-command )'

        warning = self.preprocessor.get_warning_message(original, transformed)

        assert 'WARNING' in warning
        assert 'problematic shell options' in warning
        assert 'set -euo pipefail' in warning
        assert 'subshell' in warning
        assert original.strip() in warning
        assert transformed.strip() in warning

    def test_edge_cases(self):
        """Test edge cases and potential false positives."""
        # Commands that contain 'set' but are not problematic
        assert not self.preprocessor.is_problematic_command('upset the apple cart')
        assert not self.preprocessor.is_problematic_command('reset the database')
        assert not self.preprocessor.is_problematic_command('asset management')

        # Commands with set in strings
        assert not self.preprocessor.is_problematic_command('echo "set -e"')
        assert not self.preprocessor.is_problematic_command("echo 'set -e'")

        # Commands with set but different options
        assert not self.preprocessor.is_problematic_command('set -x')
        assert not self.preprocessor.is_problematic_command('set -v')
        assert not self.preprocessor.is_problematic_command('set +e')
        assert not self.preprocessor.is_problematic_command('set +u')

        # Whitespace variations
        assert self.preprocessor.is_problematic_command('  set -e  ')
        assert self.preprocessor.is_problematic_command('\tset\t-euo\tpipefail\t')
        assert self.preprocessor.is_problematic_command('\nset -e\n')

    def test_multiple_set_commands_in_one_line(self):
        """Test handling of multiple set commands in a single line."""
        command = 'set -e && echo middle && set -o pipefail'

        assert self.preprocessor.is_problematic_command(command)

        set_commands = self.preprocessor.extract_set_commands(command)
        assert len(set_commands) == 2

        transformed, was_transformed = self.preprocessor.transform_command(command)
        assert was_transformed
        assert transformed == f'( {command} )'

    def test_real_world_examples(self):
        """Test with real-world command examples."""
        examples = [
            'set -euo pipefail && npm install',
            'set -e; ./configure && make && make install',
            "#!/bin/bash\nset -euo pipefail\necho 'Starting script'",
            'export PATH=/usr/local/bin:$PATH && set -e && python setup.py install',
        ]

        for example in examples:
            assert self.preprocessor.is_problematic_command(example)
            transformed, was_transformed = self.preprocessor.transform_command(example)
            assert was_transformed
            assert transformed == f'( {example} )'

    def test_performance_with_long_commands(self):
        """Test performance with very long commands."""
        # Create a long command without problematic set
        long_safe_command = ' && '.join([f"echo 'step {i}'" for i in range(100)])
        assert not self.preprocessor.is_problematic_command(long_safe_command)

        # Create a long command with problematic set
        long_problematic_command = f'set -e && {long_safe_command}'
        assert self.preprocessor.is_problematic_command(long_problematic_command)

        transformed, was_transformed = self.preprocessor.transform_command(
            long_problematic_command
        )
        assert was_transformed
        assert transformed == f'( {long_problematic_command} )'
