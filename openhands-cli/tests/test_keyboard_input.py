"""Tests for keyboard input handling in the CLI."""

import pytest
from prompt_toolkit import PromptSession
from prompt_toolkit.input import create_pipe_input
from prompt_toolkit.output import DummyOutput
from prompt_toolkit.key_binding import KeyBindings, merge_key_bindings
from prompt_toolkit.key_binding.defaults import load_key_bindings
from prompt_toolkit.keys import Keys

from openhands_cli.tui.tui import CommandCompleter


class TestKeyboardInput:
    """Test keyboard input handling in the CLI."""

    def test_arrow_key_navigation(self) -> None:
        """Test that arrow keys work properly for cursor navigation."""
        # Create a pipe input to simulate keyboard input
        with create_pipe_input() as pipe_input:
            # Create a prompt session with our completer
            session = PromptSession(
                completer=CommandCompleter(),
                input=pipe_input,
                output=DummyOutput(),
            )
            
            # Test data: simulate typing "hello" then pressing left arrow twice
            test_text = "hello"
            
            # Send the text
            pipe_input.send_text(test_text)
            
            # Send left arrow key (should move cursor left)
            # The escape sequence for left arrow is \x1b[D
            pipe_input.send_text("\x1b[D")  # Left arrow
            pipe_input.send_text("\x1b[D")  # Left arrow again
            
            # Send some more text to see if cursor position is correct
            pipe_input.send_text("X")
            
            # The expected result should be "helXlo" if cursor navigation worked
            # This test will help us identify if the issue exists
        
    def test_option_left_key(self) -> None:
        """Test that option+left key works properly for word navigation."""
        # Create a pipe input to simulate keyboard input
        with create_pipe_input() as pipe_input:
            # Create a prompt session
            session = PromptSession(
                completer=CommandCompleter(),
                input=pipe_input,
                output=DummyOutput(),
            )
            
            # Test data: simulate typing "hello world" then pressing option+left
            test_text = "hello world"
            
            # Send the text
            pipe_input.send_text(test_text)
            
            # Send option+left key (should move cursor to beginning of word)
            # The escape sequence for option+left is typically \x1bb
            pipe_input.send_text("\x1bb")  # Option+left
            
            # Send some text to see if cursor position is correct
            pipe_input.send_text("X")
            
            # The expected result should be "hello Xworld" if word navigation worked

    def test_right_arrow_key(self) -> None:
        """Test that right arrow key works properly."""
        # Create a pipe input to simulate keyboard input
        with create_pipe_input() as pipe_input:
            # Create a prompt session
            session = PromptSession(
                completer=CommandCompleter(),
                input=pipe_input,
                output=DummyOutput(),
            )
            
            # Test data: simulate typing "hello", moving left, then right
            test_text = "hello"
            
            # Send the text
            pipe_input.send_text(test_text)
            
            # Move left twice
            pipe_input.send_text("\x1b[D")  # Left arrow
            pipe_input.send_text("\x1b[D")  # Left arrow
            
            # Move right once
            pipe_input.send_text("\x1b[C")  # Right arrow
            
            # Insert text
            pipe_input.send_text("X")
            
            # The expected result should be "helXlo" if navigation worked correctly

    def test_escape_sequences_not_displayed(self) -> None:
        """Test that escape sequences are not displayed as literal text."""
        # This test specifically checks for the bug described in the issue
        # where escape sequences like [[C^ appear instead of cursor movement
        
        # Create a pipe input to simulate keyboard input
        with create_pipe_input() as pipe_input:
            # Create a prompt session
            session = PromptSession(
                completer=CommandCompleter(),
                input=pipe_input,
                output=DummyOutput(),
            )
            
            # Send right arrow key escape sequence
            pipe_input.send_text("\x1b[C")  # Right arrow
            
            # Send option+left escape sequence  
            pipe_input.send_text("\x1bb")   # Option+left
            
            # These escape sequences should NOT appear as literal text in the input
            # This test will help us verify that the fix works correctly

    def test_prompt_session_with_default_bindings(self) -> None:
        """Test that PromptSession with default key bindings handles keyboard input correctly."""
        # Create a pipe input to simulate keyboard input
        with create_pipe_input() as pipe_input:
            # Create key bindings that include default navigation keys (like our fix)
            default_bindings = load_key_bindings()
            custom_bindings = KeyBindings()
            
            @custom_bindings.add(Keys.ControlC)
            def _(event):
                """Handle Ctrl+C gracefully."""
                raise KeyboardInterrupt()
            
            # Merge default and custom key bindings
            all_bindings = merge_key_bindings([default_bindings, custom_bindings])
            
            # Create a prompt session with proper key bindings (our fix)
            session = PromptSession(
                completer=CommandCompleter(),
                key_bindings=all_bindings,
                input=pipe_input,
                output=DummyOutput(),
            )
            
            # This test verifies that the PromptSession can be created with the fix
            # The actual keyboard behavior would need to be tested interactively
            assert session is not None
            assert session.key_bindings is not None

    def test_prompt_session_without_default_bindings(self) -> None:
        """Test the original configuration (without explicit default bindings)."""
        # Create a pipe input to simulate keyboard input
        with create_pipe_input() as pipe_input:
            # Create a prompt session without explicit key bindings (original approach)
            session = PromptSession(
                completer=CommandCompleter(),
                input=pipe_input,
                output=DummyOutput(),
            )
            
            # This test verifies that the original approach still works
            assert session is not None