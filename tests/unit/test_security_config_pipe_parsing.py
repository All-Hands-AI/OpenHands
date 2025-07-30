"""Unit tests for pipe command parsing in security config."""

from openhands.core.config.security_config import ApprovedCommandPattern, SecurityConfig


class TestSecurityConfigPipeParsing:
    """Test pipe command parsing functionality in SecurityConfig."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = SecurityConfig()

        # Add some basic approved patterns
        self.config.add_approved_pattern(
            r'^ls( -[a-zA-Z]+)?( \S+)?$', 'List directory contents'
        )
        self.config.add_approved_pattern(
            r'^grep( -[a-zA-Z]+)? \S+( \S+)?$', 'Search text patterns'
        )
        self.config.add_approved_pattern(
            r'^head( -\d+)?( \S+)?$', 'Show first lines of file'
        )
        self.config.add_approved_pattern(
            r'^tail( -\d+)?( \S+)?$', 'Show last lines of file'
        )
        self.config.add_approved_pattern(r'^cat( \S+)?$', 'Display file contents')
        self.config.add_approved_pattern(
            r'^wc( -[a-zA-Z]+)?( \S+)?$', 'Count lines/words/chars'
        )

        # Add some exact approved commands
        self.config.approve_command('git status')
        self.config.approve_command('pwd')

    def test_simple_commands(self):
        """Test approval of simple (non-piped) commands."""
        # Should be approved
        assert self.config.is_command_approved('ls -la')
        assert self.config.is_command_approved('grep test file.txt')
        assert self.config.is_command_approved('git status')
        assert self.config.is_command_approved('pwd')
        assert self.config.is_command_approved('cat file.txt')
        assert self.config.is_command_approved('head -10')

        # Should not be approved
        assert not self.config.is_command_approved('rm -rf /')
        assert not self.config.is_command_approved('unknown_command')
        assert not self.config.is_command_approved('')

    def test_piped_commands_approved(self):
        """Test approval of piped commands where all parts are approved."""
        # Two-part pipes
        assert self.config.is_command_approved('ls -la | grep .py')
        assert self.config.is_command_approved('cat file.txt | head -10')
        assert self.config.is_command_approved('pwd | cat')

        # Three-part pipes
        assert self.config.is_command_approved('ls -la | grep .py | head -5')
        assert self.config.is_command_approved('cat file.txt | head -10 | tail -5')

    def test_piped_commands_rejected(self):
        """Test rejection of piped commands where some parts are not approved."""
        # One unapproved command in pipe
        assert not self.config.is_command_approved('ls -la | rm -rf /')
        assert not self.config.is_command_approved('cat file.txt | rm file.txt')
        assert not self.config.is_command_approved('unknown_command | grep test')
        assert not self.config.is_command_approved('ls -la | unknown_command')

        # Multiple unapproved commands
        assert not self.config.is_command_approved('rm -rf / | unknown_command')

    def test_invalid_pipe_syntax(self):
        """Test rejection of commands with invalid pipe syntax."""
        # Empty command
        assert not self.config.is_command_approved('')

        # Pipes at start or end
        assert not self.config.is_command_approved('| grep test')
        assert not self.config.is_command_approved('ls |')

        # Double pipes
        assert not self.config.is_command_approved('ls || grep')

        # Empty parts
        assert not self.config.is_command_approved('ls | | grep')

    def test_parse_piped_command(self):
        """Test the internal pipe parsing method."""
        # Simple commands
        assert self.config._parse_piped_command('ls -la') == ['ls -la']
        assert self.config._parse_piped_command('grep test') == ['grep test']

        # Piped commands
        assert self.config._parse_piped_command('ls -la | grep .py') == [
            'ls -la',
            'grep .py',
        ]
        assert self.config._parse_piped_command('cat file.txt | head -10') == [
            'cat file.txt',
            'head -10',
        ]
        assert self.config._parse_piped_command('ls | grep test | head -5') == [
            'ls',
            'grep test',
            'head -5',
        ]

        # Invalid syntax
        assert self.config._parse_piped_command('') == []
        assert self.config._parse_piped_command('| grep test') == []
        assert self.config._parse_piped_command('ls |') == []
        assert self.config._parse_piped_command('ls || grep') == []

    def test_single_command_approval(self):
        """Test the internal single command approval method."""
        # Approved commands
        assert self.config._is_single_command_approved('ls -la')
        assert self.config._is_single_command_approved('grep test file.txt')
        assert self.config._is_single_command_approved('git status')

        # Unapproved commands
        assert not self.config._is_single_command_approved('rm -rf /')
        assert not self.config._is_single_command_approved('unknown_command')

    def test_complex_piped_commands(self):
        """Test complex piped commands with various scenarios."""
        # Add more patterns for complex testing
        self.config.add_approved_pattern(r'^find \S+ -name \S+$', 'Find files by name')
        self.config.add_approved_pattern(
            r'^xargs grep \S+$', 'Execute grep on input'
        )  # More specific pattern
        self.config.add_approved_pattern(r'^sort( -[a-zA-Z]+)?$', 'Sort lines')
        self.config.add_approved_pattern(r'^uniq( -[a-zA-Z]+)?$', 'Remove duplicates')

        # Complex approved pipes
        assert self.config.is_command_approved(
            'find . -name "*.py" | xargs grep import'
        )
        assert self.config.is_command_approved('ls -la | grep .txt | sort | uniq')

        # Complex rejected pipes (one unapproved command)
        assert not self.config.is_command_approved('find . -name "*.py" | xargs rm')

    def test_whitespace_handling(self):
        """Test handling of commands with various whitespace patterns."""
        # Extra whitespace around pipes
        assert self.config.is_command_approved('ls -la  |  grep .py')
        assert self.config.is_command_approved('ls -la|grep .py')
        assert self.config.is_command_approved('  ls -la | grep .py  ')

        # Invalid due to empty parts
        assert not self.config.is_command_approved('ls -la |  | grep .py')

    def test_quoted_strings_in_pipes(self):
        """Test handling of quoted strings in piped commands."""
        # Add pattern for commands with quoted arguments
        self.config.add_approved_pattern(r'^echo .+$', 'Echo text')
        # Update grep pattern to handle quoted strings better
        self.config.add_approved_pattern(r'^grep .+ \S+$', 'Search with any pattern')

        # Commands with quotes should be parsed correctly
        assert self.config.is_command_approved('echo "hello world" | cat')
        assert self.config.is_command_approved('grep "test pattern" file.txt | head -5')

    def test_edge_cases(self):
        """Test various edge cases."""
        # Single character commands
        self.config.approve_command('w')
        assert self.config.is_command_approved('w')
        assert self.config.is_command_approved('w | cat')

        # Commands with numbers
        assert self.config.is_command_approved('head -123 file.txt')
        assert self.config.is_command_approved('tail -456 file.txt')

        # Commands with special characters (but not pipes)
        self.config.approve_command('ls -la /tmp')
        assert self.config.is_command_approved('ls -la /tmp')


class TestApprovedCommandPattern:
    """Test the ApprovedCommandPattern class."""

    def test_pattern_matching(self):
        """Test pattern matching functionality."""
        pattern = ApprovedCommandPattern(
            pattern=r'^ls( -[a-zA-Z]+)?( \S+)?$', description='List directory contents'
        )

        # Should match
        assert pattern.matches('ls')
        assert pattern.matches('ls -la')
        assert pattern.matches('ls /tmp')
        assert pattern.matches('ls -la /tmp')

        # Should not match
        assert not pattern.matches('ls -la /tmp extra')
        assert not pattern.matches('grep test')
        assert not pattern.matches('')

    def test_compiled_pattern_property(self):
        """Test the compiled_pattern property."""
        pattern = ApprovedCommandPattern(pattern=r'^test$', description='Test pattern')

        compiled = pattern.compiled_pattern
        assert compiled.pattern == r'^test$'
        assert compiled.match('test')
        assert not compiled.match('testing')
