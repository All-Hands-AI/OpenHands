#!/usr/bin/env python3
"""
Tests for get_session_prompter functionality in OpenHands CLI.
"""

import time
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

import pytest
from prompt_toolkit.input.defaults import create_pipe_input
from prompt_toolkit.output.defaults import DummyOutput
from prompt_toolkit.formatted_text import HTML

from openhands_cli.user_actions.utils import get_session_prompter
from tests.utils import _send_keys


class TestSessionPrompter:
    """Test suite for get_session_prompter functionality."""

    def test_get_session_prompter_basic_input(self) -> None:
        """Test that get_session_prompter handles basic single-line input."""
        with create_pipe_input() as pipe:
            output = DummyOutput()
            session = get_session_prompter(input=pipe, output=output)

            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(session.prompt, HTML("<gold>> </gold>"))
                
                # Send basic text and enter
                _send_keys(pipe, "hello world\r")
                
                result = future.result(timeout=2.0)
                assert result == "hello world"

    def test_get_session_prompter_multiline_with_backslash_enter(self) -> None:
        """Test that get_session_prompter handles multiline input with backslash+enter."""
        with create_pipe_input() as pipe:
            output = DummyOutput()
            session = get_session_prompter(input=pipe, output=output)

            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(session.prompt, HTML("<gold>> </gold>"))
                
                # Send text with backslash+enter for newline, then more text, then enter
                _send_keys(pipe, "line 1\\\r")  # backslash + enter
                time.sleep(0.1)  # Give time for the newline to be processed
                _send_keys(pipe, "line 2\r")  # final enter to submit
                
                result = future.result(timeout=2.0)
                assert result == "line 1\nline 2"

    def test_get_session_prompter_multiple_multiline_segments(self) -> None:
        """Test that get_session_prompter handles multiple multiline segments."""
        with create_pipe_input() as pipe:
            output = DummyOutput()
            session = get_session_prompter(input=pipe, output=output)

            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(session.prompt, HTML("<gold>> </gold>"))
                
                # Send multiple lines with backslash+enter
                _send_keys(pipe, "first line\\\r")  # backslash + enter
                time.sleep(0.1)
                _send_keys(pipe, "second line\\\r")  # backslash + enter
                time.sleep(0.1)
                _send_keys(pipe, "third line\r")  # final enter to submit
                
                result = future.result(timeout=2.0)
                assert result == "first line\nsecond line\nthird line"

    def test_get_session_prompter_empty_input(self) -> None:
        """Test that get_session_prompter handles empty input."""
        with create_pipe_input() as pipe:
            output = DummyOutput()
            session = get_session_prompter(input=pipe, output=output)

            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(session.prompt, HTML("<gold>> </gold>"))
                
                # Send just enter
                _send_keys(pipe, "\r")
                
                result = future.result(timeout=2.0)
                assert result == ""

    def test_get_session_prompter_backslash_only_then_text(self) -> None:
        """Test that get_session_prompter handles backslash+enter followed by text."""
        with create_pipe_input() as pipe:
            output = DummyOutput()
            session = get_session_prompter(input=pipe, output=output)

            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(session.prompt, HTML("<gold>> </gold>"))
                
                # Send backslash+enter first, then text
                _send_keys(pipe, "\\\r")  # backslash + enter for newline
                time.sleep(0.1)
                _send_keys(pipe, "after newline\r")  # text + enter to submit
                
                result = future.result(timeout=2.0)
                assert result == "\nafter newline"

    def test_get_session_prompter_keyboard_interrupt(self) -> None:
        """Test that get_session_prompter handles Ctrl+C (KeyboardInterrupt)."""
        with create_pipe_input() as pipe:
            output = DummyOutput()
            session = get_session_prompter(input=pipe, output=output)

            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(session.prompt, HTML("<gold>> </gold>"))
                
                # Send Ctrl+C
                _send_keys(pipe, "\x03")  # Ctrl+C
                
                with pytest.raises(KeyboardInterrupt):
                    future.result(timeout=2.0)

    def test_get_session_prompter_mixed_content_with_multiline(self) -> None:
        """Test that get_session_prompter handles mixed content with multiline."""
        with create_pipe_input() as pipe:
            output = DummyOutput()
            session = get_session_prompter(input=pipe, output=output)

            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(session.prompt, HTML("<gold>> </gold>"))
                
                # Send complex multiline input
                _send_keys(pipe, "def function():\\\r")  # backslash + enter
                time.sleep(0.1)
                _send_keys(pipe, "    return 'hello'\\\r")  # backslash + enter
                time.sleep(0.1)
                _send_keys(pipe, "    # end of function\r")  # final enter to submit
                
                result = future.result(timeout=2.0)
                expected = "def function():\n    return 'hello'\n    # end of function"
                assert result == expected

    def test_get_session_prompter_whitespace_preservation(self) -> None:
        """Test that get_session_prompter preserves whitespace in multiline input."""
        with create_pipe_input() as pipe:
            output = DummyOutput()
            session = get_session_prompter(input=pipe, output=output)

            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(session.prompt, HTML("<gold>> </gold>"))
                
                # Send input with various whitespace
                _send_keys(pipe, "  indented line\\\r")  # backslash + enter
                time.sleep(0.1)
                _send_keys(pipe, "\\\r")  # empty line with backslash + enter
                time.sleep(0.1)
                _send_keys(pipe, "    more indented\r")  # final enter to submit
                
                result = future.result(timeout=2.0)
                assert result == "  indented line\n\n    more indented"

    def test_get_session_prompter_special_characters(self) -> None:
        """Test that get_session_prompter handles special characters in multiline input."""
        with create_pipe_input() as pipe:
            output = DummyOutput()
            session = get_session_prompter(input=pipe, output=output)

            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(session.prompt, HTML("<gold>> </gold>"))
                
                # Send input with special characters
                _send_keys(pipe, "echo 'hello world'\\\r")  # backslash + enter
                time.sleep(0.1)
                _send_keys(pipe, "grep -n \"pattern\" file.txt\r")  # final enter to submit
                
                result = future.result(timeout=2.0)
                assert result == "echo 'hello world'\ngrep -n \"pattern\" file.txt"

    def test_get_session_prompter_default_parameters(self) -> None:
        """Test that get_session_prompter works with default parameters (no input/output)."""
        # This test just ensures the function can be called without parameters
        # and returns a PromptSession object
        session = get_session_prompter()
        
        # Verify it's a PromptSession with the expected configuration
        assert session is not None
        assert session.multiline is True
        assert session.key_bindings is not None
        assert session.completer is not None
        
        # Verify the prompt continuation function
        continuation = session.prompt_continuation
        assert continuation is not None
        assert continuation(80, 1, False) == "..."