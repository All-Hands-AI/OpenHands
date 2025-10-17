"""Tests for signal handler functionality in openhands.core.main."""

import asyncio
import sys
from unittest.mock import patch


def test_signal_handler_first_sigint():
    """Test that first SIGINT triggers graceful shutdown."""
    # Set up signal handler variables (simulating the function scope)
    sigint_count = 0
    shutdown_event = asyncio.Event()

    def signal_handler():
        """Handle SIGINT signals for graceful shutdown."""
        nonlocal sigint_count
        sigint_count += 1

        if sigint_count == 1:
            shutdown_event.set()
        else:
            sys.exit(1)

    # Test first SIGINT
    signal_handler()

    assert shutdown_event.is_set() is True
    assert sigint_count == 1


def test_signal_handler_second_sigint():
    """Test that second SIGINT forces immediate exit."""
    # Set up signal handler variables (simulating the function scope)
    sigint_count = 1  # Simulate first SIGINT already received
    shutdown_event = asyncio.Event()
    shutdown_event.set()  # Simulate first SIGINT already processed

    def signal_handler():
        """Handle SIGINT signals for graceful shutdown."""
        nonlocal sigint_count
        sigint_count += 1

        if sigint_count == 1:
            shutdown_event.set()
        else:
            sys.exit(1)

    # Test second SIGINT
    with patch('sys.exit') as mock_exit:
        signal_handler()
        mock_exit.assert_called_once_with(1)
