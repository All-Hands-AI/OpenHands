"""Unit tests for CLI runtime directory error handling."""

import tempfile
from pathlib import Path

from openhands.events.action import FileReadAction
from openhands.events.event import FileReadSource
from openhands.events.observation import ErrorObservation, FileReadObservation
from openhands.runtime.impl.cli.cli_runtime import CLIRuntime


class TestCLIRuntimeDirectoryHandling:
    """Test CLI runtime directory error handling."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_dir = Path(self.temp_dir) / 'test_directory'
        self.test_dir.mkdir()

        self.test_file = Path(self.temp_dir) / 'test_file.txt'
        self.test_file.write_text('This is a test file.')

        # Create minimal runtime instance
        self.runtime = CLIRuntime.__new__(CLIRuntime)
        self.runtime._runtime_initialized = True
        self.runtime._workspace_path = self.temp_dir

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir)

    def test_read_directory_returns_error(self):
        """Test that reading a directory returns proper error message."""
        action = FileReadAction(path=str(self.test_dir))
        result = self.runtime.read(action)

        assert isinstance(result, ErrorObservation)
        assert 'Cannot read directory' in result.content
        assert str(self.test_dir) in result.content

    def test_read_nonexistent_file_returns_error(self):
        """Test that reading a non-existent file returns proper error message."""
        nonexistent_file = Path(self.temp_dir) / 'nonexistent.txt'
        action = FileReadAction(path=str(nonexistent_file))
        result = self.runtime.read(action)

        assert isinstance(result, ErrorObservation)
        assert 'File not found' in result.content
        assert str(nonexistent_file) in result.content

    def test_read_valid_file_succeeds(self):
        """Test that reading a valid file works correctly."""
        action = FileReadAction(path=str(self.test_file))
        result = self.runtime.read(action)

        assert isinstance(result, FileReadObservation)
        assert 'This is a test file' in result.content

    def test_read_directory_with_oh_aci_returns_error(self):
        """Test that reading a directory with OH_ACI source returns proper error message."""
        action = FileReadAction(
            path=str(self.test_dir), impl_source=FileReadSource.OH_ACI
        )
        result = self.runtime.read(action)

        assert isinstance(result, ErrorObservation)
        assert 'Cannot read directory' in result.content
        assert str(self.test_dir) in result.content

    def test_read_binary_file_returns_error(self):
        """Test that reading a binary file returns proper error message."""
        # Create a binary file
        binary_file = Path(self.temp_dir) / 'test.bin'
        binary_file.write_bytes(b'\x00\x01\x02\x03')

        action = FileReadAction(path=str(binary_file))
        result = self.runtime.read(action)

        assert isinstance(result, ErrorObservation)
        assert 'ERROR_BINARY_FILE' in result.content
