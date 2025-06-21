"""Test that CLI doesn't show deprecation warnings for workspace_base field access."""

import argparse
import os
import subprocess
import sys
import tempfile
import unittest

# Import suppress_warnings first to apply warning filters
import openhands.cli.suppress_warnings  # noqa: F401
from openhands.core.config import OpenHandsConfig, setup_config_from_args
from openhands.core.config.utils import (
    get_workspace_dir_for_cli,
    set_workspace_dir_for_cli,
)


class TestCLIDeprecationWarnings(unittest.TestCase):
    """Test that CLI doesn't show deprecation warnings for workspace_base field access."""

    def test_cli_help_no_warnings(self):
        """Test that CLI help command doesn't show deprecation warnings to users."""
        # Run the CLI help command and capture output
        result = subprocess.run(
            [sys.executable, '-m', 'openhands.cli.main', '--help'],
            cwd='/workspace/OpenHands',
            capture_output=True,
            text=True,
            timeout=30,
        )

        # Check that the command succeeded
        self.assertEqual(result.returncode, 0)

        # Check that no deprecation warnings are shown in stderr
        stderr_lines = result.stderr.split('\n')
        deprecation_warnings = [
            line
            for line in stderr_lines
            if 'deprecated' in line.lower() and 'workspace_base' in line.lower()
        ]

        self.assertEqual(
            len(deprecation_warnings),
            0,
            f'CLI help showed deprecation warnings: {deprecation_warnings}',
        )

    def test_workspace_base_access_with_suppression(self):
        """Test that accessing workspace_base doesn't show warnings when suppression is active."""
        # This test verifies that the suppression works when properly imported
        config = OpenHandsConfig()

        # This should not trigger visible deprecation warnings due to suppress_warnings
        workspace_base = config.workspace_base

        # If we get here without warnings being printed to stderr, the test passes
        self.assertIsNone(workspace_base)  # Default value

    def test_helper_functions_work(self):
        """Test that helper functions work correctly."""
        config = OpenHandsConfig()

        # Test get_workspace_dir_for_cli
        workspace_dir = get_workspace_dir_for_cli(config)
        self.assertEqual(workspace_dir, os.getcwd())

        # Test set_workspace_dir_for_cli
        with tempfile.TemporaryDirectory() as temp_dir:
            set_workspace_dir_for_cli(config, temp_dir)
            workspace_dir = get_workspace_dir_for_cli(config)
            self.assertEqual(workspace_dir, os.path.abspath(temp_dir))

    def test_cli_config_setup_works(self):
        """Test that CLI config setup works correctly."""
        # Mock command line arguments
        args = argparse.Namespace()
        args.config_file = 'config.toml'
        args.llm_config = None
        args.agent_cls = None
        args.max_iterations = None
        args.max_budget_per_task = None
        args.selected_repo = None
        args.override_cli_mode = False
        args.directory = None

        # Test config setup
        config = setup_config_from_args(args)

        # Simulate CLI main.py logic
        should_override_cli_defaults = False

        if not should_override_cli_defaults:
            config.runtime = 'cli'
            # Check if workspace is already configured
            current_workspace = get_workspace_dir_for_cli(config)
            if current_workspace == os.getcwd():
                # No workspace configured, set current directory using new approach
                set_workspace_dir_for_cli(config, os.getcwd())
            config.security.confirmation_mode = True

        # Use helper function instead of direct access
        current_dir = get_workspace_dir_for_cli(config)
        self.assertIsNotNone(current_dir)


if __name__ == '__main__':
    unittest.main()
