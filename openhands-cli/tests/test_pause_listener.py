#!/usr/bin/env python3
"""
Tests for pause listener in OpenHands CLI.
"""

import time
from unittest.mock import MagicMock

from openhands_cli.listeners.pause_listener import PauseListener, pause_listener
from prompt_toolkit.input.defaults import create_pipe_input

from openhands.sdk import Conversation


class TestPauseListener:
    """Test suite for PauseListener class."""

    def test_pause_listener_stop(self) -> None:
        """Test PauseListener stop functionality."""
        mock_callback = MagicMock()
        listener = PauseListener(on_pause=mock_callback)

        listener.start()

        # Initially not paused
        assert not listener.is_paused()
        assert listener.is_alive()

        # Stop the listener
        listener.stop()

        # Listner was shutdown not paused
        assert not listener.is_paused()
        assert listener.is_stopped()

    def test_pause_listener_context_manager(self) -> None:
        """Test pause_listener context manager."""
        mock_conversation = MagicMock(spec=Conversation)
        mock_conversation.pause = MagicMock()

        with create_pipe_input() as pipe:
            with pause_listener(mock_conversation, pipe) as listener:
                assert isinstance(listener, PauseListener)
                assert listener.on_pause == mock_conversation.pause
                # Listener should be started (daemon thread)
                assert listener.is_alive()
                assert not listener.is_paused()
                pipe.send_text('\x10')  # Ctrl-P
                time.sleep(0.1)
                assert listener.is_paused()

            assert listener.is_stopped()
            assert not listener.is_alive()
