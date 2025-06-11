import os
import pathlib
import subprocess
import unittest
from unittest import mock

# Ensure the main module can be imported if tests are run from a different CWD
# This might need adjustment based on your project's specific PYTHONPATH setup for tests
try:
    from openhands.cli import main as cli_main
except ImportError:
    # Attempt a relative import if the above fails (common in some structures)
    # This assumes 'tests' is at the same level as 'openhands'
    import sys
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent.parent.parent))
    from openhands.cli import main as cli_main

class TestVSCodeExtensionInstall(unittest.TestCase):

    @mock.patch('pathlib.Path.exists')
    @mock.patch('pathlib.Path.touch')
    @mock.patch('pathlib.Path.mkdir')
    @mock.patch('subprocess.run')
    @mock.patch('builtins.print') # To capture print statements
    def run_test_scenario(
        self,
        mock_print,
        mock_subprocess_run,
        mock_mkdir,
        mock_touch,
        mock_path_exists,
        term_program_env=None,
        flag_file_exists=False,
        subprocess_return_value=None,
        subprocess_side_effect=None,
        expected_subprocess_called=True
    ):
        """Helper function to run test scenarios with different configurations."""
        original_env = os.environ.copy()
        if term_program_env:
            os.environ['TERM_PROGRAM'] = term_program_env
        elif 'TERM_PROGRAM' in os.environ:
            del os.environ['TERM_PROGRAM']

        mock_path_exists.return_value = flag_file_exists
        if subprocess_side_effect:
            mock_subprocess_run.side_effect = subprocess_side_effect
        elif subprocess_return_value:
            mock_subprocess_run.return_value = subprocess_return_value
        else: # Default successful run
             mock_subprocess_run.return_value = subprocess.CompletedProcess(args=[], returncode=0, stdout='', stderr='')


        cli_main.attempt_vscode_extension_install()

        if expected_subprocess_called:
            mock_subprocess_run.assert_called_once_with(
                ['code', '--install-extension', 'openhands.openhands-vscode', '--force'],
                capture_output=True,
                text=True,
                check=False,
            )
            mock_touch.assert_called_once() # Flag file should be touched
        else:
            mock_subprocess_run.assert_not_called()
            mock_touch.assert_not_called() # Flag file should not be touched if not attempted

        # Restore original environment
        os.environ.clear()
        os.environ.update(original_env)
        return mock_print # Return for asserting print calls

    def test_not_in_vscode_terminal(self):
        """Should not attempt install if not in VS Code terminal."""
        self.run_test_scenario(term_program_env='other_terminal', expected_subprocess_called=False)

    def test_flag_file_exists(self):
        """Should not attempt install if flag file already exists."""
        self.run_test_scenario(term_program_env='vscode', flag_file_exists=True, expected_subprocess_called=False)

    def test_successful_install_attempt(self):
        """Test successful execution of 'code --install-extension'."""
        mock_print_calls = self.run_test_scenario(
            term_program_env='vscode',
            subprocess_return_value=subprocess.CompletedProcess(args=[], returncode=0, stdout='Success', stderr='')
        )
        self.assertTrue(any("installation command sent successfully" in call.args[0] for call in mock_print_calls.call_args_list))

    def test_install_attempt_code_command_fails(self):
        """Test 'code --install-extension' fails (non-zero exit code)."""
        mock_print_calls = self.run_test_scenario(
            term_program_env='vscode',
            subprocess_return_value=subprocess.CompletedProcess(args=[], returncode=1, stdout='', stderr='Error installing')
        )
        self.assertTrue(any("might have failed" in call.args[0] for call in mock_print_calls.call_args_list))

    def test_install_attempt_code_not_found(self):
        """Test 'code' command not found (FileNotFoundError)."""
        mock_print_calls = self.run_test_scenario(
            term_program_env='vscode',
            subprocess_side_effect=FileNotFoundError("code not found")
        )
        self.assertTrue(any("'code' command not found" in call.args[0] for call in mock_print_calls.call_args_list))

    @mock.patch('openhands.cli.main.logger')
    def test_flag_dir_creation_os_error(self, mock_logger):
        """Test OSError during flag directory creation."""
        with mock.patch('pathlib.Path.mkdir', side_effect=OSError("Permission denied")):
            # Need to call the function directly as helper modifies mocks
            original_env = os.environ.copy()
            os.environ['TERM_PROGRAM'] = 'vscode'
            cli_main.attempt_vscode_extension_install()
            os.environ.clear()
            os.environ.update(original_env)
            mock_logger.warning.assert_called_once()
            self.assertTrue("Could not create or check VS Code extension flag directory" in mock_logger.warning.call_args[0][0])


    @mock.patch('openhands.cli.main.logger')
    def test_flag_file_touch_os_error(self, mock_logger):
        """Test OSError during flag file touch."""
        # This test needs to be structured carefully to allow the subprocess.run mock to be set up by the helper,
        # but then have the touch fail.
        original_env = os.environ.copy()
        os.environ['TERM_PROGRAM'] = 'vscode'

        with mock.patch('pathlib.Path.exists', return_value=False), \
             mock.patch('pathlib.Path.mkdir'), \
             mock.patch('subprocess.run', return_value=subprocess.CompletedProcess(args=[], returncode=0, stdout='', stderr='')), \
             mock.patch('builtins.print'), \
             mock.patch('pathlib.Path.touch', side_effect=OSError("Cannot touch")):

            cli_main.attempt_vscode_extension_install()

        os.environ.clear()
        os.environ.update(original_env)
        mock_logger.warning.assert_called_once()
        self.assertTrue("Could not create VS Code extension attempt flag file" in mock_logger.warning.call_args[0][0])


if __name__ == '__main__':
    unittest.main()
