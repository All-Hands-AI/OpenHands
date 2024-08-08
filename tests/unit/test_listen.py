import pytest
from unittest.mock import patch, MagicMock
from opendevin.server.listen import load_file_upload_config, session_manager
from opendevin.server.session import SessionManager
from opendevin.core.config import AppConfig

@pytest.fixture
def mock_config():
    return MagicMock(spec=AppConfig)

def test_load_file_upload_config(mock_config):
    with patch('opendevin.server.listen.config', mock_config):
        mock_config.file_uploads_max_file_size_mb = 10
        mock_config.file_uploads_restrict_file_types = True
        mock_config.file_uploads_allowed_extensions = ['.txt', '.pdf']

        max_size, restrict_types, allowed_extensions = load_file_upload_config()

        assert max_size == 10
        assert restrict_types is True
        assert set(allowed_extensions) == {'.txt', '.pdf'}

def test_load_file_upload_config_invalid_max_size(mock_config):
    with patch('opendevin.server.listen.config', mock_config):
        mock_config.file_uploads_max_file_size_mb = -5
        mock_config.file_uploads_restrict_file_types = False
        mock_config.file_uploads_allowed_extensions = []

        max_size, restrict_types, allowed_extensions = load_file_upload_config()

        assert max_size == 0  # Should default to 0 when invalid
        assert restrict_types is False
        assert allowed_extensions == []

def test_session_manager_initialization():
    assert isinstance(session_manager, SessionManager)

# Add more tests here as needed
