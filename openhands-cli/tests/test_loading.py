#!/usr/bin/env python3
"""
Unit tests for the loading animation functionality.
"""

import threading
import time
import unittest
from unittest.mock import patch

from openhands_cli.listeners.loading_listener import (
    LoadingContext,
    display_initialization_animation,
)


class TestLoadingAnimation(unittest.TestCase):
    """Test cases for loading animation functionality."""

    def test_loading_context_manager(self):
        """Test that LoadingContext works as a context manager."""
        with LoadingContext('Test loading...') as ctx:
            self.assertIsInstance(ctx, LoadingContext)
            self.assertEqual(ctx.text, 'Test loading...')
            self.assertIsInstance(ctx.is_loaded, threading.Event)
            self.assertIsNotNone(ctx.loading_thread)
            # Give the thread a moment to start
            time.sleep(0.1)
            self.assertTrue(ctx.loading_thread.is_alive())

        # After exiting context, thread should be stopped
        time.sleep(0.1)
        self.assertFalse(ctx.loading_thread.is_alive())

    @patch('sys.stdout')
    def test_animation_writes_while_running_and_stops_after(self, mock_stdout):
        """Ensure stdout is written while animation runs and stops after it ends."""
        is_loaded = threading.Event()

        animation_thread = threading.Thread(
            target=display_initialization_animation,
            args=('Test output', is_loaded),
            daemon=True,
        )
        animation_thread.start()

        # Let it run a bit and check calls
        time.sleep(0.2)
        calls_while_running = mock_stdout.write.call_count
        self.assertGreater(calls_while_running, 0, 'Expected writes while spinner runs')

        # Stop animation
        is_loaded.set()
        time.sleep(0.2)

        animation_thread.join(timeout=1.0)
        calls_after_stop = mock_stdout.write.call_count

        # Wait a moment to detect any stray writes after thread finished
        time.sleep(0.2)
        self.assertEqual(
            calls_after_stop,
            mock_stdout.write.call_count,
            'No extra writes should occur after animation stops',
        )


if __name__ == '__main__':
    unittest.main()
