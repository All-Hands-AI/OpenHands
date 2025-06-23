import os
import pathlib
import subprocess
from unittest import mock

import pytest

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

@pytest.fixture
def original_env():
    """Fixture to preserve and restore environment variables."""
    original = os.environ.copy()
    yield original
    os.environ.clear()
    os.environ.update(original)


def clear_windsurf_environment():
    """Helper function to clear all windsurf-related environment variables."""
    # Find all keys that contain windsurf in their name OR value
    windsurf_keys = []
    for key, val in os.environ.items():
        if 'windsurf' in key.lower() or (isinstance(val, str) and 'windsurf' in val.lower()):
            windsurf_keys.append(key)
    
    for key in ['TERM_PROGRAM', '__CFBundleIdentifier'] + windsurf_keys:
        if key in os.environ:
            del os.environ[key]
    
    # Set a clean PATH without windsurf references
    os.environ['PATH'] = '/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin'


@mock.patch('pathlib.Path.exists')
@mock.patch('pathlib.Path.touch')
@mock.patch('pathlib.Path.mkdir')
@mock.patch('subprocess.run')
@mock.patch('builtins.print')  # To capture print statements
def run_test_scenario(
    mock_print,
    mock_subprocess_run,
    mock_mkdir,
    mock_touch,
    mock_path_exists,
    term_program_env=None,
    is_windsurf=False,
    flag_file_exists=False,
    subprocess_return_value=None,
    subprocess_side_effect=None,
    expected_subprocess_called=True
):
    """Helper function to run test scenarios with different configurations."""
    original_env = os.environ.copy()
    
    # Clear environment first
    clear_windsurf_environment()
    
    # Set up environment based on test parameters
    if term_program_env:
        os.environ['TERM_PROGRAM'] = term_program_env
    
    if is_windsurf:
        os.environ['__CFBundleIdentifier'] = 'com.exafunction.windsurf'
        expected_command = 'surf'
    else:
        expected_command = 'code'

    mock_path_exists.return_value = flag_file_exists
    if subprocess_side_effect:
        mock_subprocess_run.side_effect = subprocess_side_effect
    elif subprocess_return_value:
        mock_subprocess_run.return_value = subprocess_return_value
    else:  # Default successful run
        mock_subprocess_run.return_value = subprocess.CompletedProcess(args=[], returncode=0, stdout='', stderr='')

    cli_main.attempt_vscode_extension_install()

    if expected_subprocess_called:
        # The function now tries bundled .vsix first, then marketplace
        # We need to check that at least one call was made with the expected command
        calls = mock_subprocess_run.call_args_list
        assert len(calls) >= 1, f"Expected at least one subprocess call, got {len(calls)}"
        
        # Check that at least one call uses the expected command
        found_expected_call = False
        for call in calls:
            args, kwargs = call
            if args[0][0] == expected_command:
                found_expected_call = True
                break
        
        assert found_expected_call, f"Expected call with command '{expected_command}', but got calls: {calls}"
        mock_touch.assert_called_once()  # Flag file should be touched
    else:
        mock_subprocess_run.assert_not_called()
        mock_touch.assert_not_called()  # Flag file should not be touched if not attempted

    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)
    return mock_print  # Return for asserting print calls

def test_not_in_vscode_terminal():
    """Should not attempt install if not in VS Code terminal."""
    run_test_scenario(term_program_env='other_terminal', expected_subprocess_called=False)


def test_flag_file_exists_vscode():
    """Should not attempt install if flag file already exists (VS Code)."""
    run_test_scenario(term_program_env='vscode', flag_file_exists=True, expected_subprocess_called=False)


def test_flag_file_exists_windsurf():
    """Should not attempt install if flag file already exists (Windsurf)."""
    run_test_scenario(is_windsurf=True, flag_file_exists=True, expected_subprocess_called=False)


def test_successful_install_attempt_vscode():
    """Test successful execution of 'code --install-extension'."""
    mock_print_calls = run_test_scenario(
        term_program_env='vscode',
        subprocess_return_value=subprocess.CompletedProcess(args=[], returncode=0, stdout='Success', stderr='')
    )
    assert any("OpenHands VS Code extension installed successfully" in call.args[0] for call in mock_print_calls.call_args_list)


def test_successful_install_attempt_windsurf():
    """Test successful execution of 'surf --install-extension'."""
    mock_print_calls = run_test_scenario(
        is_windsurf=True,
        subprocess_return_value=subprocess.CompletedProcess(args=[], returncode=0, stdout='Success', stderr='')
    )
    assert any("OpenHands Windsurf extension installed successfully" in call.args[0] for call in mock_print_calls.call_args_list)


def test_install_attempt_code_command_fails():
    """Test 'code --install-extension' fails (non-zero exit code)."""
    mock_print_calls = run_test_scenario(
        term_program_env='vscode',
        subprocess_return_value=subprocess.CompletedProcess(args=[], returncode=1, stdout='', stderr='Error installing')
    )
    assert any("may require your confirmation in VS Code" in call.args[0] for call in mock_print_calls.call_args_list)


def test_install_attempt_code_not_found():
    """Test 'code' command not found (FileNotFoundError)."""
    mock_print_calls = run_test_scenario(
        term_program_env='vscode',
        subprocess_side_effect=FileNotFoundError("code not found")
    )
    assert any("ensure the 'code' command-line tool is in your PATH" in call.args[0] for call in mock_print_calls.call_args_list)

@mock.patch('openhands.cli.main.logger')
def test_flag_dir_creation_os_error_vscode(mock_logger):
    """Test OSError during flag directory creation (VS Code)."""
    with mock.patch('pathlib.Path.mkdir', side_effect=OSError("Permission denied")):
        # Need to call the function directly as helper modifies mocks
        original_env = os.environ.copy()
        clear_windsurf_environment()
        os.environ['TERM_PROGRAM'] = 'vscode'
        cli_main.attempt_vscode_extension_install()
        os.environ.clear()
        os.environ.update(original_env)
        mock_logger.warning.assert_called_once()
        assert "Could not create or check VS Code extension flag directory" in mock_logger.warning.call_args[0][0]


@mock.patch('openhands.cli.main.logger')
def test_flag_dir_creation_os_error_windsurf(mock_logger):
    """Test OSError during flag directory creation (Windsurf)."""
    with mock.patch('pathlib.Path.mkdir', side_effect=OSError("Permission denied")):
        # Need to call the function directly as helper modifies mocks
        original_env = os.environ.copy()
        clear_windsurf_environment()
        os.environ['__CFBundleIdentifier'] = 'com.exafunction.windsurf'
        cli_main.attempt_vscode_extension_install()
        os.environ.clear()
        os.environ.update(original_env)
        mock_logger.warning.assert_called_once()
        assert "Could not create or check Windsurf extension flag directory" in mock_logger.warning.call_args[0][0]


@mock.patch('openhands.cli.main.logger')
def test_flag_file_touch_os_error_vscode(mock_logger):
    """Test OSError during flag file touch (VS Code)."""
    # This test needs to be structured carefully to allow the subprocess.run mock to be set up by the helper,
    # but then have the touch fail.
    original_env = os.environ.copy()
    clear_windsurf_environment()
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
    assert "Could not create VS Code extension attempt flag file" in mock_logger.warning.call_args[0][0]


@mock.patch('openhands.cli.main.logger')
def test_flag_file_touch_os_error_windsurf(mock_logger):
    """Test OSError during flag file touch (Windsurf)."""
    # This test needs to be structured carefully to allow the subprocess.run mock to be set up by the helper,
    # but then have the touch fail.
    original_env = os.environ.copy()
    clear_windsurf_environment()
    os.environ['__CFBundleIdentifier'] = 'com.exafunction.windsurf'

    with mock.patch('pathlib.Path.exists', return_value=False), \
         mock.patch('pathlib.Path.mkdir'), \
         mock.patch('subprocess.run', return_value=subprocess.CompletedProcess(args=[], returncode=0, stdout='', stderr='')), \
         mock.patch('builtins.print'), \
         mock.patch('pathlib.Path.touch', side_effect=OSError("Cannot touch")):

        cli_main.attempt_vscode_extension_install()

    os.environ.clear()
    os.environ.update(original_env)
    mock_logger.warning.assert_called_once()
    assert "Could not create Windsurf extension attempt flag file" in mock_logger.warning.call_args[0][0]
