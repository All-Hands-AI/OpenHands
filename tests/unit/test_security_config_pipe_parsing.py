"""Tests for the security config pipe parsing functionality."""

import pytest
import bashlex

from openhands.security.command_approval.analyzer import CommandParser


class TestBashlexParsing:
    """Test bashlex parsing functionality."""

    def test_bashlex_pipe_detection(self):
        """Test detection of piped commands using bashlex."""
        parser = CommandParser()
        
        # Commands with pipes
        assert parser.is_piped_command("ls -la | grep .py")
        assert parser.is_piped_command("cat file.txt | head -10 | tail -5")
        assert parser.is_piped_command("find . -name '*.py' | xargs grep 'import'")
        
        # Commands without pipes
        assert not parser.is_piped_command("ls -la")
        assert not parser.is_piped_command("echo 'hello world'")
        assert not parser.is_piped_command("ls -la > output.txt")
        
        # Edge cases
        assert not parser.is_piped_command("")
        # Pipe in quotes is not a real pipe
        assert not parser.is_piped_command("echo 'hello | world'")
        
    def test_bashlex_command_extraction(self):
        """Test extraction of commands from pipelines using bashlex."""
        parser = CommandParser()
        
        # Simple command
        assert parser.parse_command("ls -la") == ["ls -la"]
        
        # Piped commands
        assert parser.parse_command("ls -la | grep .py") == ["ls -la", "grep .py"]
        assert parser.parse_command("cat file.txt | head -10 | tail -5") == ["cat file.txt", "head -10", "tail -5"]
        
        # Commands with redirections
        assert parser.parse_command("ls -la > output.txt") == ["ls -la"]
        
        # Edge cases
        assert parser.parse_command("") == []
        assert parser.parse_command("echo 'hello | world'") == ["echo hello | world"]