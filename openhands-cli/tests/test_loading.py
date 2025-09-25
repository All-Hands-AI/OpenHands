#!/usr/bin/env python3
"""
Unit tests for the loading animation functionality.
"""

import threading
import time
import unittest
from unittest.mock import patch

from openhands_cli.loading import LoadingContext, display_initialization_animation


class TestLoadingAnimation(unittest.TestCase):
    """Test cases for loading animation functionality."""

    def test_loading_context_manager(self):
        """Test that LoadingContext works as a context manager."""
        with LoadingContext("Test loading...") as ctx:
            self.assertIsInstance(ctx, LoadingContext)
            self.assertEqual(ctx.text, "Test loading...")
            self.assertIsInstance(ctx.is_loaded, threading.Event)
            self.assertIsNotNone(ctx.loading_thread)
            # Give the thread a moment to start
            time.sleep(0.1)
            self.assertTrue(ctx.loading_thread.is_alive())

        # After exiting context, thread should be stopped
        time.sleep(0.1)
        self.assertFalse(ctx.loading_thread.is_alive())

    def test_display_initialization_animation_stops_when_loaded(self):
        """Test that animation stops when is_loaded event is set."""
        is_loaded = threading.Event()

        # Start animation in a separate thread
        animation_thread = threading.Thread(
            target=display_initialization_animation,
            args=("Test animation", is_loaded),
            daemon=True
        )
        animation_thread.start()

        # Let it run for a short time
        time.sleep(0.2)
        self.assertTrue(animation_thread.is_alive())

        # Signal that loading is complete
        is_loaded.set()

        # Wait for thread to finish
        animation_thread.join(timeout=1.0)
        self.assertFalse(animation_thread.is_alive())

    @patch('sys.stdout')
    def test_animation_writes_to_stdout(self, mock_stdout):
        """Test that animation writes to stdout."""
        is_loaded = threading.Event()

        # Start animation
        animation_thread = threading.Thread(
            target=display_initialization_animation,
            args=("Test output", is_loaded),
            daemon=True
        )
        animation_thread.start()

        # Let it run briefly
        time.sleep(0.15)

        # Stop animation
        is_loaded.set()
        animation_thread.join(timeout=1.0)

        # Verify stdout.write was called
        self.assertTrue(mock_stdout.write.called)
        self.assertTrue(mock_stdout.flush.called)


if __name__ == "__main__":
    unittest.main()
