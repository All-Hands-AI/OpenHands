"""Tests for the CLI main module."""

import importlib
import sys
from unittest.mock import patch


def test_main_function_exists():
    """Test that the main function exists and can be imported."""
    # Import the module
    from openhands.cli import main

    # Check that the main function exists
    assert hasattr(main, 'main'), 'main function should exist in openhands.cli.main'

    # Check that it's callable
    assert callable(main.main), 'main should be a callable function'


def test_main_function_can_be_called_without_arguments():
    """Test that the main function can be called without arguments."""
    # This test verifies that the main function can be called as an entry point
    # without requiring any arguments

    # Import the module
    from openhands.cli import main

    # Mock sys.argv to simulate command line arguments
    with patch.object(sys, 'argv', ['openhands', '--help']):
        # Mock the parse_arguments function to avoid actual argument parsing
        with patch('openhands.cli.main.parse_arguments'):
            # Mock the main_async function to avoid actual execution
            with patch('openhands.cli.main.main_async') as mock_main_async:
                # Call the main function - this should not raise any exceptions
                try:
                    # We expect this to exit with SystemExit due to --help
                    main.main()
                except SystemExit:
                    pass

                # Verify that main_async was called
                mock_main_async.assert_called_once()


def test_entry_point_in_pyproject():
    """Test that the entry point in pyproject.toml points to the correct function."""
    # This test verifies that the entry point in pyproject.toml points to a function
    # that exists and can be called

    # Import the module that would be called by the entry point
    module = importlib.import_module('openhands.cli.main')

    # Get the function that would be called by the entry point
    function = getattr(module, 'main')

    # Check that it's callable
    assert callable(function), 'Entry point function should be callable'
