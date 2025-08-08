"""Tests for command pattern generation and parsing."""

import re
from unittest.mock import MagicMock, patch

import pytest

from openhands.cli.tui import (
    _generate_command_patterns,
    _generate_single_command_pattern,
    _handle_pattern_selection,
    _parse_piped_command,
    read_confirmation_input,
)


class TestGenerateSingleCommandPattern:
    """Test the _generate_single_command_pattern function."""

    def test_empty_command(self):
        """Test pattern generation for empty command."""
        patterns = _generate_single_command_pattern('')
        assert len(patterns) == 1
        assert patterns[0] == '^$'

    def test_single_word_command(self):
        """Test pattern generation for single word command."""
        patterns = _generate_single_command_pattern('ls')
        assert len(patterns) == 1
        assert patterns[0] == '^ls(\\s.*|$)'

    def test_two_word_command(self):
        """Test pattern generation for two word command."""
        patterns = _generate_single_command_pattern('ls -la')
        assert len(patterns) == 2
        assert patterns[0] == '^ls(\\s.*|$)'
        assert patterns[1] == '^ls\\s+\\-la.*$'

    def test_three_word_command(self):
        """Test pattern generation for three word command."""
        patterns = _generate_single_command_pattern('git commit -m')
        assert len(patterns) == 3
        assert patterns[0] == '^git(\\s.*|$)'
        assert patterns[1] == '^git\\s+commit.*$'
        assert patterns[2] == '^git\\s+commit\\s+\\-m.*$'

    def test_four_word_command(self):
        """Test pattern generation for four word command (should only generate 3 patterns)."""
        patterns = _generate_single_command_pattern('git commit -m message')
        assert len(patterns) == 3  # Only first 3 prefixes
        assert patterns[0] == '^git(\\s.*|$)'
        assert patterns[1] == '^git\\s+commit.*$'
        assert patterns[2] == '^git\\s+commit\\s+\\-m.*$'

    def test_pattern_matching(self):
        """Test that generated patterns actually match similar commands."""
        patterns = _generate_single_command_pattern('ls -la')

        # Test first pattern (ls.*)
        pattern1 = re.compile(patterns[0])
        assert pattern1.match('ls')
        assert pattern1.match('ls -la')
        assert pattern1.match('ls -alh /home')
        assert not pattern1.match('cat file.txt')

        # Test second pattern (ls -la.*)
        pattern2 = re.compile(patterns[1])
        assert pattern2.match('ls -la')
        assert pattern2.match('ls -la /home')
        assert not pattern2.match('ls')
        assert not pattern2.match('ls -alh')

    def test_special_characters_escaped(self):
        """Test that special regex characters are properly escaped."""
        patterns = _generate_single_command_pattern('echo $HOME')
        assert len(patterns) == 2
        assert patterns[0] == '^echo(\\s.*|$)'
        assert patterns[1] == '^echo\\s+\\$HOME.*$'

        # Test that the pattern works
        pattern = re.compile(patterns[1])
        assert pattern.match('echo $HOME')
        assert pattern.match('echo $HOME/test')


class TestParsePipedCommand:
    """Test the _parse_piped_command function."""

    def test_empty_command(self):
        """Test parsing empty command."""
        result = _parse_piped_command('')
        assert result == []

    def test_whitespace_only_command(self):
        """Test parsing whitespace-only command."""
        result = _parse_piped_command('   ')
        assert result == []

    def test_single_command(self):
        """Test parsing single command without pipes."""
        result = _parse_piped_command('ls -la')
        assert result == ['ls -la']

    def test_simple_piped_command(self):
        """Test parsing simple piped command."""
        result = _parse_piped_command('ls -la | grep test')
        assert result == ['ls -la', 'grep test']

    def test_three_command_pipe(self):
        """Test parsing three-command pipe."""
        result = _parse_piped_command('cat file.txt | grep pattern | wc -l')
        assert result == ['cat file.txt', 'grep pattern', 'wc -l']

    def test_pipe_with_quotes(self):
        """Test parsing piped command with quoted arguments."""
        result = _parse_piped_command('echo "hello world" | grep "hello"')
        # shlex removes quotes, so we get the unquoted content
        assert result == ['echo hello world', 'grep hello']

    def test_pipe_without_spaces(self):
        """Test parsing piped command without spaces around pipes."""
        result = _parse_piped_command('ls|grep test')
        assert result == ['ls', 'grep test']

    def test_complex_command_with_options(self):
        """Test parsing complex command with various options."""
        result = _parse_piped_command(
            "find /home -name '*.py' | xargs grep -l 'import os'"
        )
        # shlex removes quotes, so we get the unquoted content
        assert result == ['find /home -name *.py', 'xargs grep -l import os']

    def test_invalid_quotes(self):
        """Test parsing command with invalid quotes falls back gracefully."""
        result = _parse_piped_command('echo "unclosed quote | grep test')
        assert result == ['echo "unclosed quote', 'grep test']


class TestGenerateCommandPatterns:
    """Test the _generate_command_patterns function."""

    def test_single_command(self):
        """Test pattern generation for single command."""
        patterns = _generate_command_patterns('ls -la')
        assert len(patterns) == 2
        assert patterns[0] == '^ls(\\s.*|$)'
        assert patterns[1] == '^ls\\s+\\-la.*$'

    def test_piped_command(self):
        """Test pattern generation for piped command."""
        patterns = _generate_command_patterns('ls -la | grep test')
        assert len(patterns) == 1
        # Should combine the first pattern from each sub-command
        assert patterns[0] == '^ls(\\s.*|$)\\s*\\|\\s*grep(\\s.*|$)$'

    def test_empty_command(self):
        """Test pattern generation for empty command."""
        patterns = _generate_command_patterns('')
        assert len(patterns) == 1
        assert patterns[0] == '^$'


class TestReadConfirmationInput:
    """Test the read_confirmation_input function."""

    @pytest.mark.asyncio
    @patch('openhands.cli.tui.cli_confirm')
    async def test_yes_option(self, mock_confirm):
        """Test selecting 'yes' option."""
        mock_confirm.return_value = 0  # First option (Yes, proceed)

        config = MagicMock()
        config.cli = MagicMock(vi_mode=False)

        result = await read_confirmation_input(config=config, command='ls -la')
        assert result == 'yes'

    @pytest.mark.asyncio
    @patch('openhands.cli.tui.cli_confirm')
    async def test_no_option(self, mock_confirm):
        """Test selecting 'no' option."""
        mock_confirm.return_value = 1  # Second option (No)

        config = MagicMock()
        config.cli = MagicMock(vi_mode=False)

        result = await read_confirmation_input(config=config, command='ls -la')
        assert result == 'no'

    @pytest.mark.asyncio
    @patch('openhands.cli.tui.cli_confirm')
    async def test_always_option(self, mock_confirm):
        """Test selecting 'always' option."""
        mock_confirm.return_value = 2  # Third option (Always proceed)

        config = MagicMock()
        config.cli = MagicMock(vi_mode=False)

        result = await read_confirmation_input(config=config, command='ls -la')
        assert result == 'always'

    @pytest.mark.asyncio
    @patch('openhands.cli.tui._handle_pattern_selection')
    @patch('openhands.cli.tui.cli_confirm')
    async def test_remember_option(self, mock_confirm, mock_pattern_selection):
        """Test selecting 'remember' option."""
        mock_confirm.return_value = 3  # Fourth option (Remember)
        mock_pattern_selection.return_value = (
            'remember:^ls.*$:Commands starting with: ls'
        )

        config = MagicMock()
        config.cli = MagicMock(vi_mode=False)

        result = await read_confirmation_input(config=config, command='ls -la')
        assert result == 'remember:^ls.*$:Commands starting with: ls'
        mock_pattern_selection.assert_called_once_with(config, 'ls -la')


class TestHandlePatternSelection:
    """Test the _handle_pattern_selection function."""

    @pytest.mark.asyncio
    @patch('openhands.cli.tui.cli_confirm')
    async def test_exact_command_selection(self, mock_confirm):
        """Test selecting exact command pattern."""
        mock_confirm.return_value = 0  # First option (exact command)

        config = MagicMock()
        config.cli = MagicMock(vi_mode=False)

        result = await _handle_pattern_selection(config, 'ls -la')
        assert result.startswith('remember:^ls\\ \\-la$:Exact command: ls -la')

    @pytest.mark.asyncio
    @patch('openhands.cli.tui.cli_confirm')
    async def test_prefix_pattern_selection(self, mock_confirm):
        """Test selecting prefix pattern."""
        mock_confirm.return_value = 1  # Second option (first prefix pattern)

        config = MagicMock()
        config.cli = MagicMock(vi_mode=False)

        result = await _handle_pattern_selection(config, 'ls -la')
        assert result.startswith('remember:^ls(\\s.*|$):Commands starting with: ls')

    @pytest.mark.asyncio
    @patch('openhands.cli.tui.create_prompt_session')
    @patch('openhands.cli.tui.cli_confirm')
    async def test_custom_pattern_selection_valid(
        self, mock_confirm, mock_create_session
    ):
        """Test selecting custom pattern with valid regex."""
        mock_confirm.return_value = (
            3  # Custom pattern option (assuming 3 total options)
        )

        # Mock the prompt session
        mock_session = MagicMock()

        # Create a proper async mock
        async def mock_prompt_async(prompt):
            return '^git.*$'

        mock_session.prompt_async = mock_prompt_async
        mock_create_session.return_value = mock_session

        config = MagicMock()
        config.cli = MagicMock(vi_mode=False)

        result = await _handle_pattern_selection(config, 'ls -la')
        assert result == 'remember:^git.*$:Custom pattern: ^git.*$'

    @pytest.mark.asyncio
    @patch('openhands.cli.tui.create_prompt_session')
    @patch('openhands.cli.tui.cli_confirm')
    @patch('openhands.cli.tui.print_formatted_text')
    async def test_custom_pattern_selection_invalid(
        self, mock_print, mock_confirm, mock_create_session
    ):
        """Test selecting custom pattern with invalid regex."""
        mock_confirm.return_value = 3  # Custom pattern option

        # Mock the prompt session to return invalid regex
        mock_session = MagicMock()

        # Create a proper async mock
        async def mock_prompt_async(prompt):
            return '[invalid regex'

        mock_session.prompt_async = mock_prompt_async
        mock_create_session.return_value = mock_session

        config = MagicMock()
        config.cli = MagicMock(vi_mode=False)

        result = await _handle_pattern_selection(config, 'ls -la')
        # Should fall back to exact command
        assert result.startswith('remember:^ls\\ \\-la$:Exact command: ls -la')
        # Should print error message
        mock_print.assert_called()


class TestPatternMatching:
    """Test that the generated patterns work correctly for matching commands."""

    def test_ls_patterns(self):
        """Test patterns generated for ls command."""
        patterns = _generate_single_command_pattern('ls -alh')

        # Test first pattern (ls.*)
        pattern1 = re.compile(patterns[0])
        assert pattern1.match('ls')
        assert pattern1.match('ls -la')
        assert pattern1.match('ls -alh /home')
        assert pattern1.match('ls --help')
        assert not pattern1.match('cat file.txt')
        assert not pattern1.match('lsof')  # Should not match partial word

        # Test second pattern (ls -alh.*)
        pattern2 = re.compile(patterns[1])
        assert pattern2.match('ls -alh')
        assert pattern2.match('ls -alh /home')
        assert not pattern2.match('ls')
        assert not pattern2.match('ls -la')

    def test_git_patterns(self):
        """Test patterns generated for git command."""
        patterns = _generate_single_command_pattern('git commit -m')

        # Test git(\s.*|$)
        pattern1 = re.compile(patterns[0])
        assert pattern1.match('git status')
        assert pattern1.match('git commit')
        assert pattern1.match('git push origin main')
        assert not pattern1.match('github')  # Should not match partial word

        # Test git commit.*
        pattern2 = re.compile(patterns[1])
        assert pattern2.match('git commit')
        assert pattern2.match("git commit -m 'message'")
        assert pattern2.match('git commit --amend')
        assert not pattern2.match('git status')
        assert not pattern2.match('git push')

    def test_piped_command_patterns(self):
        """Test patterns generated for piped commands."""
        patterns = _generate_command_patterns('cat file.txt | grep pattern')

        pattern = re.compile(patterns[0])
        assert pattern.match('cat file.txt | grep pattern')
        assert pattern.match('cat another.txt | grep something')
        assert pattern.match('cat /path/to/file | grep test')
        assert not pattern.match('cat file.txt')
        assert not pattern.match('grep pattern')

    def test_complex_command_patterns(self):
        """Test patterns for complex commands with special characters."""
        patterns = _generate_single_command_pattern("find /home -name '*.py'")

        # Test find(\s.*|$)
        pattern1 = re.compile(patterns[0])
        assert pattern1.match("find /home -name '*.py'")
        assert pattern1.match('find . -type f')
        assert pattern1.match('find /usr/bin -executable')
        assert not pattern1.match('finder')  # Should not match partial word

        # Test find /home.*
        pattern2 = re.compile(patterns[1])
        assert pattern2.match("find /home -name '*.py'")
        assert pattern2.match('find /home -type d')
        assert not pattern2.match("find . -name '*.py'")
        assert not pattern2.match("find /usr -name '*.py'")
