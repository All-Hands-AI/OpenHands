"""Unit tests for file reader directory error handling."""

import tempfile
from pathlib import Path

import pytest

from openhands.runtime.plugins.agent_skills.file_reader.file_readers import (
    _base64_img,
    parse_audio,
    parse_docx,
    parse_latex,
    parse_pdf,
    parse_pptx,
)


class TestFileReaderDirectoryHandling:
    """Test file reader directory error handling."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_dir = Path(self.temp_dir) / 'test_directory'
        self.test_dir.mkdir()

        self.test_file = Path(self.temp_dir) / 'test_file.txt'
        self.test_file.write_text('This is a test file.')

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir)

    def test_parse_latex_with_directory(self, capsys):
        """Test that parse_latex handles directory input gracefully."""
        parse_latex(str(self.test_dir))

        captured = capsys.readouterr()
        assert 'ERROR: Cannot read directory as LaTeX file' in captured.out
        assert str(self.test_dir) in captured.out

    def test_parse_latex_with_nonexistent_file(self, capsys):
        """Test that parse_latex handles non-existent file gracefully."""
        nonexistent_file = Path(self.temp_dir) / 'nonexistent.tex'
        parse_latex(str(nonexistent_file))

        captured = capsys.readouterr()
        assert 'ERROR: File not found' in captured.out
        assert str(nonexistent_file) in captured.out

    def test_base64_img_with_directory(self):
        """Test that _base64_img raises IsADirectoryError for directory input."""
        with pytest.raises(IsADirectoryError) as exc_info:
            _base64_img(str(self.test_dir))

        assert 'Cannot read directory as image file' in str(exc_info.value)
        assert str(self.test_dir) in str(exc_info.value)

    def test_base64_img_with_nonexistent_file(self):
        """Test that _base64_img raises FileNotFoundError for non-existent file."""
        nonexistent_file = Path(self.temp_dir) / 'nonexistent.jpg'

        with pytest.raises(FileNotFoundError) as exc_info:
            _base64_img(str(nonexistent_file))

        assert 'File not found' in str(exc_info.value)
        assert str(nonexistent_file) in str(exc_info.value)

    def test_parse_audio_with_directory(self, capsys):
        """Test that parse_audio handles directory input gracefully."""
        parse_audio(str(self.test_dir))

        captured = capsys.readouterr()
        assert 'ERROR: Cannot read directory as audio file' in captured.out
        assert str(self.test_dir) in captured.out

    def test_parse_audio_with_nonexistent_file(self, capsys):
        """Test that parse_audio handles non-existent file gracefully."""
        nonexistent_file = Path(self.temp_dir) / 'nonexistent.mp3'
        parse_audio(str(nonexistent_file))

        captured = capsys.readouterr()
        assert 'ERROR: File not found' in captured.out
        assert str(nonexistent_file) in captured.out

    def test_parse_pdf_with_directory(self, capsys):
        """Test that parse_pdf handles directory input gracefully."""
        parse_pdf(str(self.test_dir))

        captured = capsys.readouterr()
        assert 'ERROR: Cannot read directory as PDF file' in captured.out
        assert str(self.test_dir) in captured.out

    def test_parse_docx_with_directory(self, capsys):
        """Test that parse_docx handles directory input gracefully."""
        parse_docx(str(self.test_dir))

        captured = capsys.readouterr()
        assert 'ERROR: Cannot read directory as DOCX file' in captured.out
        assert str(self.test_dir) in captured.out

    def test_parse_pptx_with_directory(self, capsys):
        """Test that parse_pptx handles directory input gracefully."""
        parse_pptx(str(self.test_dir))

        captured = capsys.readouterr()
        assert 'ERROR: Cannot read directory as PowerPoint file' in captured.out
        assert str(self.test_dir) in captured.out
