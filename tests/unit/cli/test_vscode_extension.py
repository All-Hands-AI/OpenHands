import os
import pathlib
import subprocess
from unittest import mock

import pytest

from openhands.cli import vscode_extension


@pytest.fixture
def mock_env_and_dependencies():
    """A fixture to mock all external dependencies and manage the environment."""
    with mock.patch.dict(os.environ, {}, clear=True), \
         mock.patch('pathlib.Path.home') as mock_home, \
         mock.patch('pathlib.Path.exists') as mock_exists, \
         mock.patch('pathlib.Path.touch') as mock_touch, \
         mock.patch('pathlib.Path.mkdir') as mock_mkdir, \
         mock.patch('subprocess.run') as mock_subprocess, \
         mock.patch('importlib.resources.as_file') as mock_as_file, \
         mock.patch('openhands.cli.vscode_extension.download_latest_vsix_from_github') as mock_download, \
         mock.patch('builtins.print') as mock_print, \
         mock.patch('openhands.cli.vscode_extension.logger.debug') as mock_logger:

        # Setup a temporary directory for home
        temp_dir = pathlib.Path.cwd() / 'temp_test_home'
        temp_dir.mkdir(exist_ok=True)
        mock_home.return_value = temp_dir

        try:
            yield {
                'home': mock_home,
                'exists': mock_exists,
                'touch': mock_touch,
                'mkdir': mock_mkdir,
                'subprocess': mock_subprocess,
                'as_file': mock_as_file,
                'download': mock_download,
                'print': mock_print,
                'logger': mock_logger,
            }
        finally:
            # Teardown the temporary directory, ignoring errors if files don't exist
            openhands_dir = temp_dir / '.openhands'
            if openhands_dir.exists():
                for f in openhands_dir.glob('*'):
                    if f.is_file():
                        f.unlink()
                try:
                    openhands_dir.rmdir()
                except FileNotFoundError:
                    pass
            try:
                temp_dir.rmdir()
            except (FileNotFoundError, OSError):
                pass


def test_not_in_vscode_environment(mock_env_and_dependencies):
    """Should not attempt any installation if not in a VSCode-like environment."""
    os.environ['TERM_PROGRAM'] = 'not_vscode'
    vscode_extension.attempt_vscode_extension_install()
    mock_env_and_dependencies['download'].assert_not_called()
    mock_env_and_dependencies['subprocess'].assert_not_called()


def test_already_attempted_flag_prevents_execution(mock_env_and_dependencies):
    """Should do nothing if the installation flag file already exists."""
    os.environ['TERM_PROGRAM'] = 'vscode'
    mock_env_and_dependencies['exists'].return_value = True  # Simulate flag file exists
    vscode_extension.attempt_vscode_extension_install()
    mock_env_and_dependencies['download'].assert_not_called()
    mock_env_and_dependencies['subprocess'].assert_not_called()


def test_install_succeeds_from_github(mock_env_and_dependencies):
    """Should successfully install from GitHub on the first try."""
    os.environ['TERM_PROGRAM'] = 'vscode'
    mock_env_and_dependencies['exists'].return_value = False
    mock_env_and_dependencies['download'].return_value = '/fake/path/to/github.vsix'
    mock_env_and_dependencies['subprocess'].return_value = subprocess.CompletedProcess(returncode=0, args=[], stdout='', stderr='')

    with mock.patch('os.remove') as mock_os_remove:
        vscode_extension.attempt_vscode_extension_install()

        mock_env_and_dependencies['download'].assert_called_once()
        mock_env_and_dependencies['subprocess'].assert_called_once_with(
            ['code', '--install-extension', '/fake/path/to/github.vsix', '--force'],
            capture_output=True, text=True, check=False
        )
        mock_env_and_dependencies['print'].assert_any_call(
            'INFO: OpenHands VS Code extension installed successfully from GitHub.'
        )
        mock_os_remove.assert_called_once_with('/fake/path/to/github.vsix')
        mock_env_and_dependencies['touch'].assert_called_once()


def test_github_fails_falls_back_to_bundled(mock_env_and_dependencies):
    """Should fall back to bundled VSIX if GitHub download fails."""
    os.environ['TERM_PROGRAM'] = 'vscode'
    mock_env_and_dependencies['exists'].return_value = False
    mock_env_and_dependencies['download'].return_value = None

    mock_vsix_path = mock.MagicMock()
    mock_vsix_path.exists.return_value = True
    mock_vsix_path.__str__.return_value = '/fake/path/to/bundled.vsix'
    mock_env_and_dependencies['as_file'].return_value.__enter__.return_value = mock_vsix_path
    mock_env_and_dependencies['subprocess'].return_value = subprocess.CompletedProcess(returncode=0, args=[], stdout='', stderr='')

    vscode_extension.attempt_vscode_extension_install()

    mock_env_and_dependencies['download'].assert_called_once()
    mock_env_and_dependencies['as_file'].assert_called_once()
    mock_env_and_dependencies['subprocess'].assert_called_once_with(
        ['code', '--install-extension', '/fake/path/to/bundled.vsix', '--force'],
        capture_output=True, text=True, check=False
    )
    mock_env_and_dependencies['touch'].assert_called_once()


def test_all_methods_fail(mock_env_and_dependencies):
    """Should show a final failure message if all installation methods fail."""
    os.environ['TERM_PROGRAM'] = 'vscode'
    mock_env_and_dependencies['exists'].return_value = False
    mock_env_and_dependencies['download'].return_value = None
    mock_env_and_dependencies['as_file'].side_effect = FileNotFoundError
    mock_env_and_dependencies['subprocess'].return_value = subprocess.CompletedProcess(returncode=1, args=[], stdout='', stderr='Error')

    vscode_extension.attempt_vscode_extension_install()

    mock_env_and_dependencies['download'].assert_called_once()
    mock_env_and_dependencies['as_file'].assert_called_once()
    assert mock_env_and_dependencies['subprocess'].call_count == 1
    mock_env_and_dependencies['print'].assert_any_call(
        "INFO: Automatic installation failed. Please install 'openhands.openhands-vscode' manually from the VS Code Marketplace."
    )
    mock_env_and_dependencies['touch'].assert_called_once()

def test_windsurf_detection_and_install(mock_env_and_dependencies):
    """Should correctly detect Windsurf and use the 'surf' command."""
    os.environ['__CFBundleIdentifier'] = 'com.exafunction.windsurf'
    mock_env_and_dependencies['exists'].return_value = False
    mock_env_and_dependencies['download'].return_value = None
    mock_env_and_dependencies['as_file'].side_effect = FileNotFoundError
    mock_env_and_dependencies['subprocess'].return_value = subprocess.CompletedProcess(returncode=0, args=[], stdout='', stderr='')

    vscode_extension.attempt_vscode_extension_install()

    mock_env_and_dependencies['subprocess'].assert_called_once_with(
        ['surf', '--install-extension', 'openhands.openhands-vscode', '--force'],
        capture_output=True, text=True, check=False
    )
    mock_env_and_dependencies['print'].assert_any_call(
        'INFO: Windsurf extension installed successfully from the Marketplace.'
    )
    mock_env_and_dependencies['touch'].assert_called_once()