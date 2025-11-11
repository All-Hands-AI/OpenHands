"""Tests for TUI functionality."""

from openhands_cli.tui.tui import COMMANDS, CommandCompleter
from prompt_toolkit.completion import CompleteEvent
from prompt_toolkit.document import Document


class TestCommandCompleter:
    """Test the CommandCompleter class."""

    def test_command_completion_with_slash(self) -> None:
        """Test that commands are completed when starting with /."""
        completer = CommandCompleter()
        document = Document('/')
        completions = list(completer.get_completions(document, CompleteEvent()))

        # Should return all available commands
        assert len(completions) == len(COMMANDS)

        # Check that all commands are included
        completion_texts = [c.text for c in completions]
        for command in COMMANDS.keys():
            assert command in completion_texts

    def test_command_completion_partial_match(self) -> None:
        """Test that partial command matches work correctly."""
        completer = CommandCompleter()
        document = Document('/ex')
        completions = list(completer.get_completions(document, CompleteEvent()))

        # Should return only /exit
        assert len(completions) == 1
        assert completions[0].text == '/exit'
        # display_meta is a FormattedText object, so we need to check its content
        # Extract the text from FormattedText
        meta_text = completions[0].display_meta
        if hasattr(meta_text, '_formatted_text'):
            # Extract text from FormattedText
            text_content = ''.join([item[1] for item in meta_text._formatted_text])
        else:
            text_content = str(meta_text)
        assert COMMANDS['/exit'] in text_content

    def test_command_completion_no_slash(self) -> None:
        """Test that no completions are returned without /."""
        completer = CommandCompleter()
        document = Document('help')
        completions = list(completer.get_completions(document, CompleteEvent()))

        # Should return no completions
        assert len(completions) == 0

    def test_command_completion_no_match(self) -> None:
        """Test that no completions are returned for non-matching commands."""
        completer = CommandCompleter()
        document = Document('/nonexistent')
        completions = list(completer.get_completions(document, CompleteEvent()))

        # Should return no completions
        assert len(completions) == 0

    def test_command_completion_styling(self) -> None:
        """Test that completions have proper styling."""
        completer = CommandCompleter()
        document = Document('/help')
        completions = list(completer.get_completions(document, CompleteEvent()))

        assert len(completions) == 1
        completion = completions[0]
        assert completion.style == 'bg:ansidarkgray fg:gold'
        assert completion.start_position == -5  # Length of "/help"


def test_commands_dict() -> None:
    """Test that COMMANDS dictionary contains expected commands."""
    expected_commands = {
        '/exit',
        '/help',
        '/clear',
        '/new',
        '/status',
        '/confirm',
        '/resume',
        '/settings',
        '/mcp',
    }
    assert set(COMMANDS.keys()) == expected_commands

    # Check that all commands have descriptions
    for command, description in COMMANDS.items():
        assert isinstance(command, str)
        assert command.startswith('/')
        assert isinstance(description, str)
        assert len(description) > 0
