import os
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

from openhands.cli.vscode_extension import attempt_vscode_extension_install


class TestVscodeExtension:
    def setup_method(self):
        self.temp_dir = Path.cwd() / 'temp_test_home'
        self.temp_dir.mkdir(exist_ok=True)
        self.openhands_dir = self.temp_dir / '.openhands'

    def teardown_method(self):
        for f in self.openhands_dir.glob('*'):
            if f.is_file():
                f.unlink()
        if self.openhands_dir.exists():
            self.openhands_dir.rmdir()
        self.temp_dir.rmdir()

    @patch('os.remove')
    @patch('openhands.cli.vscode_extension.download_latest_vsix_from_github')
    @patch('importlib.resources.as_file')
    @patch('subprocess.run')
    @patch('pathlib.Path.home')
    def test_already_attempted_flag_prevents_execution(
        self, mock_path_home, mock_subprocess_run, mock_importlib_resources, mock_download, mock_os_remove
    ):
        mock_path_home.return_value = self.temp_dir
        with patch.dict(os.environ, {'TERM_PROGRAM': 'vscode'}, clear=True):
            self.openhands_dir.mkdir()
            (self.openhands_dir / '.vscode_extension_install_attempted').touch()

            attempt_vscode_extension_install()

            assert not mock_download.called
            assert not mock_subprocess_run.called

    @patch('os.remove')
    @patch('openhands.cli.vscode_extension.download_latest_vsix_from_github')
    @patch('importlib.resources.as_file')
    @patch('subprocess.run')
    @patch('pathlib.Path.home')
    @patch('builtins.print')
    def test_install_succeeds_from_github(
        self, mock_print, mock_path_home, mock_subprocess_run, mock_importlib_resources, mock_download, mock_os_remove
    ):
        mock_path_home.return_value = self.temp_dir
        with patch.dict(os.environ, {'TERM_PROGRAM': 'vscode'}, clear=True):
            mock_download.return_value = '/fake/path/to/github.vsix'
            mock_subprocess_run.return_value = MagicMock(returncode=0)

            attempt_vscode_extension_install()

            mock_download.assert_called_once()
            mock_subprocess_run.assert_called_once_with(
                ['code', '--install-extension', '/fake/path/to/github.vsix', '--force'],
                capture_output=True,
                text=True,
                check=False,
            )
            mock_print.assert_any_call(
                'INFO: OpenHands VS Code extension installed successfully from GitHub.'
            )
            assert (self.openhands_dir / '.vscode_extension_install_attempted').exists()

    @patch('openhands.cli.vscode_extension.download_latest_vsix_from_github')
    @patch('importlib.resources.as_file')
    @patch('subprocess.run')
    @patch('pathlib.Path.home')
    def test_github_fails_falls_back_to_bundled(
        self, mock_path_home, mock_subprocess_run, mock_importlib_resources, mock_download
    ):
        mock_path_home.return_value = self.temp_dir
        with patch.dict(os.environ, {'TERM_PROGRAM': 'vscode'}, clear=True):
            mock_download.return_value = None
            mock_vsix_path = MagicMock()
            mock_vsix_path.exists.return_value = True
            mock_vsix_path.__str__.return_value = '/fake/path/to/bundled.vsix'
            mock_importlib_resources.return_value = MagicMock(
                __enter__=MagicMock(return_value=mock_vsix_path)
            )
            mock_subprocess_run.return_value = MagicMock(returncode=0)

            attempt_vscode_extension_install()

            mock_download.assert_called_once()
            mock_importlib_resources.assert_called_once()
            mock_subprocess_run.assert_called_once_with(
                ['code', '--install-extension', '/fake/path/to/bundled.vsix', '--force'],
                capture_output=True,
                text=True,
                check=False,
            )
            assert (self.openhands_dir / '.vscode_extension_install_attempted').exists()

    @patch('openhands.cli.vscode_extension.download_latest_vsix_from_github')
    @patch('importlib.resources.as_file')
    @patch('subprocess.run')
    @patch('pathlib.Path.home')
    @patch('builtins.print')
    def test_all_methods_fail(
        self, mock_print, mock_path_home, mock_subprocess_run, mock_importlib_resources, mock_download
    ):
        mock_path_home.return_value = self.temp_dir
        with patch.dict(os.environ, {'TERM_PROGRAM': 'vscode'}, clear=True):
            mock_download.return_value = None
            mock_importlib_resources.side_effect = FileNotFoundError
            mock_subprocess_run.return_value = MagicMock(returncode=1, stderr='Error')

            attempt_vscode_extension_install()

            mock_download.assert_called_once()
            mock_importlib_resources.assert_called_once()
            assert mock_subprocess_run.call_count == 1
            mock_print.assert_any_call(
                "INFO: Automatic installation failed. Please install 'openhands.openhands-vscode' manually from the VS Code Marketplace."
            )
            assert (self.openhands_dir / '.vscode_extension_install_attempted').exists()
