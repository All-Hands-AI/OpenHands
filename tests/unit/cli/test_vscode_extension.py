import os
import pathlib
import subprocess
from unittest import mock

import pytest

from openhands.cli import vscode_extension


@pytest.fixture
def mock_env_and_dependencies():
    """A fixture to mock all external dependencies and manage the environment."""
    with (
        mock.patch.dict(os.environ, {}, clear=True),
        mock.patch('pathlib.Path.home') as mock_home,
        mock.patch('pathlib.Path.exists') as mock_exists,
        mock.patch('pathlib.Path.touch') as mock_touch,
        mock.patch('pathlib.Path.mkdir') as mock_mkdir,
        mock.patch('subprocess.run') as mock_subprocess,
        mock.patch('importlib.resources.as_file') as mock_as_file,
        mock.patch(
            'openhands.cli.vscode_extension.download_latest_vsix_from_github'
        ) as mock_download,
        mock.patch('builtins.print') as mock_print,
        mock.patch('openhands.cli.vscode_extension.logger.debug') as mock_logger,
    ):
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
    mock_env_and_dependencies['subprocess'].return_value = subprocess.CompletedProcess(
        returncode=0, args=[], stdout='', stderr=''
    )

    with mock.patch('os.remove') as mock_os_remove:
        vscode_extension.attempt_vscode_extension_install()

        mock_env_and_dependencies['download'].assert_called_once()
        mock_env_and_dependencies['subprocess'].assert_called_once_with(
            ['code', '--install-extension', '/fake/path/to/github.vsix', '--force'],
            capture_output=True,
            text=True,
            check=False,
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
    mock_env_and_dependencies[
        'as_file'
    ].return_value.__enter__.return_value = mock_vsix_path
    mock_env_and_dependencies['subprocess'].return_value = subprocess.CompletedProcess(
        returncode=0, args=[], stdout='', stderr=''
    )

    vscode_extension.attempt_vscode_extension_install()

    mock_env_and_dependencies['download'].assert_called_once()
    mock_env_and_dependencies['as_file'].assert_called_once()
    mock_env_and_dependencies['subprocess'].assert_called_once_with(
        ['code', '--install-extension', '/fake/path/to/bundled.vsix', '--force'],
        capture_output=True,
        text=True,
        check=False,
    )
    mock_env_and_dependencies['touch'].assert_called_once()


def test_all_methods_fail(mock_env_and_dependencies):
    """Should show a final failure message if all installation methods fail."""
    os.environ['TERM_PROGRAM'] = 'vscode'
    mock_env_and_dependencies['exists'].return_value = False
    mock_env_and_dependencies['download'].return_value = None
    mock_env_and_dependencies['as_file'].side_effect = FileNotFoundError
    mock_env_and_dependencies['subprocess'].return_value = subprocess.CompletedProcess(
        returncode=1, args=[], stdout='', stderr='Error'
    )

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
    mock_env_and_dependencies['subprocess'].return_value = subprocess.CompletedProcess(
        returncode=0, args=[], stdout='', stderr=''
    )

    vscode_extension.attempt_vscode_extension_install()

    mock_env_and_dependencies['subprocess'].assert_called_once_with(
        ['surf', '--install-extension', 'openhands.openhands-vscode', '--force'],
        capture_output=True,
        text=True,
        check=False,
    )
    mock_env_and_dependencies['print'].assert_any_call(
        'INFO: Windsurf extension installed successfully from the Marketplace.'
    )
    mock_env_and_dependencies['touch'].assert_called_once()


def test_os_error_on_mkdir(mock_env_and_dependencies):
    """Should log a debug message if creating the flag directory fails."""
    os.environ['TERM_PROGRAM'] = 'vscode'
    mock_env_and_dependencies['mkdir'].side_effect = OSError('Permission denied')

    vscode_extension.attempt_vscode_extension_install()

    mock_env_and_dependencies['logger'].assert_called_once_with(
        'Could not create or check VS Code extension flag directory: Permission denied'
    )
    mock_env_and_dependencies['download'].assert_not_called()


def test_os_error_on_touch(mock_env_and_dependencies):
    """Should log a debug message if creating the flag file fails."""
    os.environ['TERM_PROGRAM'] = 'vscode'
    mock_env_and_dependencies['exists'].return_value = False
    mock_env_and_dependencies['download'].return_value = None
    mock_env_and_dependencies['as_file'].side_effect = FileNotFoundError
    mock_env_and_dependencies['subprocess'].side_effect = FileNotFoundError
    mock_env_and_dependencies['touch'].side_effect = OSError('Permission denied')

    vscode_extension.attempt_vscode_extension_install()

    mock_env_and_dependencies['logger'].assert_called_with(
        'Could not create VS Code extension attempt flag file: Permission denied'
    )

def test_flag_file_exists_windsurf(mock_env_and_dependencies):
    """Should not attempt install if flag file already exists (Windsurf)."""
    os.environ['__CFBundleIdentifier'] = 'com.exafunction.windsurf'
    mock_env_and_dependencies['exists'].return_value = True
    vscode_extension.attempt_vscode_extension_install()
    mock_env_and_dependencies['download'].assert_not_called()
    mock_env_and_dependencies['subprocess'].assert_not_called()

def test_successful_install_attempt_vscode(mock_env_and_dependencies):
    """Test successful execution of 'code --install-extension'."""
    os.environ['TERM_PROGRAM'] = 'vscode'
    mock_env_and_dependencies['exists'].return_value = False
    mock_env_and_dependencies['download'].return_value = None
    mock_env_and_dependencies['as_file'].side_effect = FileNotFoundError
    mock_env_and_dependencies['subprocess'].return_value = subprocess.CompletedProcess(returncode=0, args=[], stdout='Success', stderr='')
    vscode_extension.attempt_vscode_extension_install()
    mock_env_and_dependencies['print'].assert_any_call('INFO: VS Code extension installed successfully from the Marketplace.')

def test_successful_install_attempt_windsurf(mock_env_and_dependencies):
    """Test successful execution of 'surf --install-extension'."""
    os.environ['__CFBundleIdentifier'] = 'com.exafunction.windsurf'
    mock_env_and_dependencies['exists'].return_value = False
    mock_env_and_dependencies['download'].return_value = None
    mock_env_and_dependencies['as_file'].side_effect = FileNotFoundError
    mock_env_and_dependencies['subprocess'].return_value = subprocess.CompletedProcess(returncode=0, args=[], stdout='Success', stderr='')
    vscode_extension.attempt_vscode_extension_install()
    mock_env_and_dependencies['print'].assert_any_call('INFO: Windsurf extension installed successfully from the Marketplace.')

def test_install_attempt_code_command_fails(mock_env_and_dependencies):
    """Test 'code --install-extension' fails (non-zero exit code)."""
    os.environ['TERM_PROGRAM'] = 'vscode'
    mock_env_and_dependencies['exists'].return_value = False
    mock_env_and_dependencies['download'].return_value = None
    mock_env_and_dependencies['as_file'].side_effect = FileNotFoundError
    mock_env_and_dependencies['subprocess'].return_value = subprocess.CompletedProcess(returncode=1, args=[], stdout='', stderr='Error installing')
    vscode_extension.attempt_vscode_extension_install()
    mock_env_and_dependencies['print'].assert_any_call("INFO: Automatic installation failed. Please install 'openhands.openhands-vscode' manually from the VS Code Marketplace.")

def test_install_attempt_code_not_found(mock_env_and_dependencies):
    """Test 'code' command not found (FileNotFoundError)."""
    os.environ['TERM_PROGRAM'] = 'vscode'
    mock_env_and_dependencies['exists'].return_value = False
    mock_env_and_dependencies['download'].return_value = None
    mock_env_and_dependencies['as_file'].side_effect = FileNotFoundError
    mock_env_and_dependencies['subprocess'].side_effect = FileNotFoundError("code not found")
    vscode_extension.attempt_vscode_extension_install()
    mock_env_and_dependencies['print'].assert_any_call("INFO: To complete VS Code integration, please ensure the 'code' command-line tool is in your PATH.")

def test_flag_dir_creation_os_error_windsurf(mock_env_and_dependencies):
    """Test OSError during flag directory creation (Windsurf)."""
    os.environ['__CFBundleIdentifier'] = 'com.exafunction.windsurf'
    mock_env_and_dependencies['mkdir'].side_effect = OSError('Permission denied')
    vscode_extension.attempt_vscode_extension_install()
    mock_env_and_dependencies['logger'].assert_called_once_with(
        "Could not create or check Windsurf extension flag directory: Permission denied"
    )
    mock_env_and_dependencies['download'].assert_not_called()

def test_flag_file_touch_os_error_vscode(mock_env_and_dependencies):
    """Test OSError during flag file touch (VS Code)."""
    os.environ['TERM_PROGRAM'] = 'vscode'
    mock_env_and_dependencies['exists'].return_value = False
    mock_env_and_dependencies['download'].return_value = None
    mock_env_and_dependencies['as_file'].side_effect = FileNotFoundError
    mock_env_and_dependencies['subprocess'].side_effect = FileNotFoundError
    mock_env_and_dependencies['touch'].side_effect = OSError('Permission denied')
    vscode_extension.attempt_vscode_extension_install()
    mock_env_and_dependencies['logger'].assert_called_with(
        "Could not create VS Code extension attempt flag file: Permission denied"
    )

def test_flag_file_touch_os_error_windsurf(mock_env_and_dependencies):
    """Test OSError during flag file touch (Windsurf)."""
    os.environ['__CFBundleIdentifier'] = 'com.exafunction.windsurf'
    mock_env_and_dependencies['exists'].return_value = False
    mock_env_and_dependencies['download'].return_value = None
    mock_env_and_dependencies['as_file'].side_effect = FileNotFoundError
    mock_env_and_dependencies['subprocess'].side_effect = FileNotFoundError
    mock_env_and_dependencies['touch'].side_effect = OSError('Permission denied')
    vscode_extension.attempt_vscode_extension_install()
    mock_env_and_dependencies['logger'].assert_called_with(
        "Could not create Windsurf extension attempt flag file: Permission denied"
    )

def test_bundled_vsix_installation_failure_fallback_to_marketplace(mock_env_and_dependencies):
    """Test bundled VSIX failure with successful marketplace fallback."""
    os.environ['TERM_PROGRAM'] = 'vscode'
    mock_env_and_dependencies['exists'].return_value = False
    mock_env_and_dependencies['download'].return_value = None
    mock_vsix_path = mock.MagicMock()
    mock_vsix_path.exists.return_value = True
    mock_vsix_path.__str__.return_value = '/mock/path/openhands-vscode-0.0.1.vsix'
    mock_env_and_dependencies['as_file'].return_value.__enter__.return_value = mock_vsix_path
    def subprocess_side_effect(*args, **kwargs):
        if '/mock/path/openhands-vscode-0.0.1.vsix' in str(args[0]):
            return subprocess.CompletedProcess(args=args[0], returncode=1, stdout='Installation failed', stderr='Error installing extension')
        else:
            return subprocess.CompletedProcess(args=args[0], returncode=0, stdout='Extension installed', stderr='')
    mock_env_and_dependencies['subprocess'].side_effect = subprocess_side_effect
    vscode_extension.attempt_vscode_extension_install()
    assert mock_env_and_dependencies['subprocess'].call_count == 2
    mock_env_and_dependencies['print'].assert_any_call('INFO: VS Code extension installed successfully from the Marketplace.')

def test_bundled_vsix_not_found_fallback_to_marketplace(mock_env_and_dependencies):
    """Test bundled VSIX not found with marketplace fallback."""
    os.environ['TERM_PROGRAM'] = 'vscode'
    mock_env_and_dependencies['exists'].return_value = False
    mock_env_and_dependencies['download'].return_value = None
    mock_vsix_path = mock.MagicMock()
    mock_vsix_path.exists.return_value = False
    mock_env_and_dependencies['as_file'].return_value.__enter__.return_value = mock_vsix_path
    mock_env_and_dependencies['subprocess'].return_value = subprocess.CompletedProcess(returncode=0, args=[], stdout='Extension installed', stderr='')
    vscode_extension.attempt_vscode_extension_install()
    mock_env_and_dependencies['subprocess'].assert_called_once()
    args = mock_env_and_dependencies['subprocess'].call_args[0][0]
    assert args[0] == 'code'
    assert 'openhands.openhands-vscode' in args
    mock_env_and_dependencies['print'].assert_any_call('INFO: VS Code extension installed successfully from the Marketplace.')

def test_importlib_resources_exception_fallback_to_marketplace(mock_env_and_dependencies):
    """Test importlib.resources exception with marketplace fallback."""
    os.environ['TERM_PROGRAM'] = 'vscode'
    mock_env_and_dependencies['exists'].return_value = False
    mock_env_and_dependencies['download'].return_value = None
    mock_env_and_dependencies['as_file'].side_effect = FileNotFoundError('Resource not found')
    mock_env_and_dependencies['subprocess'].return_value = subprocess.CompletedProcess(returncode=0, args=[], stdout='Extension installed', stderr='')
    vscode_extension.attempt_vscode_extension_install()
    mock_env_and_dependencies['subprocess'].assert_called_once()
    args = mock_env_and_dependencies['subprocess'].call_args[0][0]
    assert args[0] == 'code'
    assert 'openhands.openhands-vscode' in args
    mock_env_and_dependencies['print'].assert_any_call('INFO: VS Code extension installed successfully from the Marketplace.')

def test_comprehensive_windsurf_detection_path_based(mock_env_and_dependencies):
    """Test Windsurf detection via PATH environment variable."""
    os.environ['PATH'] = '/usr/local/bin:/Applications/Windsurf.app/Contents/Resources/app/bin:/usr/bin'
    mock_env_and_dependencies['exists'].return_value = False
    mock_env_and_dependencies['download'].return_value = None
    mock_env_and_dependencies['as_file'].side_effect = FileNotFoundError
    mock_env_and_dependencies['subprocess'].return_value = subprocess.CompletedProcess(returncode=0, args=[], stdout='Extension installed', stderr='')
    vscode_extension.attempt_vscode_extension_install()
    mock_env_and_dependencies['subprocess'].assert_called()
    args = mock_env_and_dependencies['subprocess'].call_args[0][0]
    assert args[0] == 'surf'
    mock_env_and_dependencies['print'].assert_any_call('INFO: Windsurf extension installed successfully from the Marketplace.')

def test_comprehensive_windsurf_detection_env_value_based(mock_env_and_dependencies):
    """Test Windsurf detection via environment variable values."""
    os.environ['SOME_APP_PATH'] = '/Applications/Windsurf.app/Contents/MacOS/Windsurf'
    mock_env_and_dependencies['exists'].return_value = False
    mock_env_and_dependencies['download'].return_value = None
    mock_env_and_dependencies['as_file'].side_effect = FileNotFoundError
    mock_env_and_dependencies['subprocess'].return_value = subprocess.CompletedProcess(returncode=0, args=[], stdout='Extension installed', stderr='')
    vscode_extension.attempt_vscode_extension_install()
    mock_env_and_dependencies['subprocess'].assert_called()
    args = mock_env_and_dependencies['subprocess'].call_args[0][0]
    assert args[0] == 'surf'
    mock_env_and_dependencies['print'].assert_any_call('INFO: Windsurf extension installed successfully from the Marketplace.')

def test_comprehensive_windsurf_detection_multiple_indicators(mock_env_and_dependencies):
    """Test Windsurf detection with multiple environment indicators."""
    os.environ['__CFBundleIdentifier'] = 'com.exafunction.windsurf'
    os.environ['PATH'] = '/usr/local/bin:/Applications/Windsurf.app/Contents/Resources/app/bin:/usr/bin'
    os.environ['WINDSURF_CONFIG'] = '/Users/test/.windsurf/config'
    mock_env_and_dependencies['exists'].return_value = False
    mock_env_and_dependencies['download'].return_value = None
    mock_env_and_dependencies['as_file'].side_effect = FileNotFoundError
    mock_env_and_dependencies['subprocess'].return_value = subprocess.CompletedProcess(returncode=0, args=[], stdout='Extension installed', stderr='')
    vscode_extension.attempt_vscode_extension_install()
    mock_env_and_dependencies['subprocess'].assert_called()
    args = mock_env_and_dependencies['subprocess'].call_args[0][0]
    assert args[0] == 'surf'
    mock_env_and_dependencies['print'].assert_any_call('INFO: Windsurf extension installed successfully from the Marketplace.')

def test_no_editor_detection_skips_installation(mock_env_and_dependencies):
    """Test that no installation is attempted when no supported editor is detected."""
    os.environ['TERM_PROGRAM'] = 'iTerm.app'
    os.environ['PATH'] = '/usr/local/bin:/usr/bin:/bin'
    vscode_extension.attempt_vscode_extension_install()
    mock_env_and_dependencies['exists'].assert_not_called()
    mock_env_and_dependencies['touch'].assert_not_called()
    mock_env_and_dependencies['subprocess'].assert_not_called()
    mock_env_and_dependencies['print'].assert_not_called()

def test_both_bundled_and_marketplace_fail(mock_env_and_dependencies):
    """Test when both bundled VSIX and marketplace installation fail."""
    os.environ['TERM_PROGRAM'] = 'vscode'
    mock_env_and_dependencies['exists'].return_value = False
    mock_env_and_dependencies['download'].return_value = None
    mock_vsix_path = mock.MagicMock()
    mock_vsix_path.exists.return_value = True
    mock_vsix_path.__str__.return_value = '/mock/path/openhands-vscode-0.0.1.vsix'
    mock_env_and_dependencies['as_file'].return_value.__enter__.return_value = mock_vsix_path
    def subprocess_side_effect(*args, **kwargs):
        if '/mock/path/openhands-vscode-0.0.1.vsix' in str(args[0]):
            return subprocess.CompletedProcess(args=args[0], returncode=1, stdout='Bundled installation failed', stderr='Error installing bundled extension')
        else:
            return subprocess.CompletedProcess(args=args[0], returncode=1, stdout='Marketplace installation failed', stderr='Error installing from marketplace')
    mock_env_and_dependencies['subprocess'].side_effect = subprocess_side_effect
    vscode_extension.attempt_vscode_extension_install()
    assert mock_env_and_dependencies['subprocess'].call_count == 2
    mock_env_and_dependencies['print'].assert_any_call("INFO: Automatic installation failed. Please install 'openhands.openhands-vscode' manually from the VS Code Marketplace.")

