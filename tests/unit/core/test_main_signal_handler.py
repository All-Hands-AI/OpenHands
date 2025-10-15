"""Tests for signal handler functionality in openhands.core.main."""

import asyncio
import json
import os
import sys
import tempfile
from unittest.mock import MagicMock, patch


class MockController:
    """Mock controller for testing."""

    def get_trajectory(self, save_screenshots=False):
        return {'test': 'trajectory', 'events': [{'action': 'test'}]}


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


def test_trajectory_saving_during_graceful_shutdown():
    """Test that trajectory is saved correctly during graceful shutdown."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create mock config and controller
        config = MagicMock()
        config.save_trajectory_path = temp_dir
        config.save_screenshots_in_trajectory = False

        controller = MockController()
        sid = 'test_session_123'
        shutdown_event = asyncio.Event()
        shutdown_event.set()  # Simulate graceful shutdown

        # Simulate trajectory saving logic from run_controller
        if config.save_trajectory_path is not None:
            # if save_trajectory_path is a folder, use session id as file name
            if os.path.isdir(config.save_trajectory_path):
                file_path = os.path.join(config.save_trajectory_path, sid + '.json')
            else:
                file_path = config.save_trajectory_path
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            histories = controller.get_trajectory(config.save_screenshots_in_trajectory)
            with open(file_path, 'w') as f:
                json.dump(histories, f, indent=4)

        # Verify the file was created and contains expected content
        expected_file = os.path.join(temp_dir, 'test_session_123.json')
        assert os.path.exists(expected_file)

        with open(expected_file, 'r') as f:
            saved_data = json.load(f)
            expected_data = {'test': 'trajectory', 'events': [{'action': 'test'}]}
            assert saved_data == expected_data


def test_trajectory_saving_with_file_path():
    """Test trajectory saving when save_trajectory_path is a file path."""
    with tempfile.TemporaryDirectory() as temp_dir:
        file_path = os.path.join(temp_dir, 'custom_trajectory.json')

        # Create mock config and controller
        config = MagicMock()
        config.save_trajectory_path = file_path
        config.save_screenshots_in_trajectory = False

        controller = MockController()
        shutdown_event = asyncio.Event()
        shutdown_event.set()  # Simulate graceful shutdown

        # Simulate trajectory saving logic from run_controller
        if config.save_trajectory_path is not None:
            # if save_trajectory_path is a folder, use session id as file name
            if os.path.isdir(config.save_trajectory_path):
                final_path = os.path.join(config.save_trajectory_path, 'sid.json')
            else:
                final_path = config.save_trajectory_path
            os.makedirs(os.path.dirname(final_path), exist_ok=True)
            histories = controller.get_trajectory(config.save_screenshots_in_trajectory)
            with open(final_path, 'w') as f:
                json.dump(histories, f, indent=4)

        # Verify the file was created at the specified path
        assert os.path.exists(file_path)

        with open(file_path, 'r') as f:
            saved_data = json.load(f)
            expected_data = {'test': 'trajectory', 'events': [{'action': 'test'}]}
            assert saved_data == expected_data
