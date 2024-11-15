import os
import tempfile
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from openhands.core.config import AppConfig, LLMConfig, SandboxConfig


# Mock the SessionManager to avoid asyncio issues
class MockSessionManager:
    def __init__(self, *args, **kwargs):
        pass


# Mock StaticFiles
class MockStaticFiles:
    def __init__(self, *args, **kwargs):
        pass


# Patch necessary components before importing from listen
with patch('openhands.server.session.SessionManager', MockSessionManager), patch(
    'fastapi.staticfiles.StaticFiles', MockStaticFiles
):
    from openhands.server.listen import (
        app,
        is_extension_allowed,
        load_file_upload_config,
    )


def test_load_file_upload_config():
    config = AppConfig(
        file_uploads_max_file_size_mb=10,
        file_uploads_restrict_file_types=True,
        file_uploads_allowed_extensions=['.txt', '.pdf'],
    )
    with patch('openhands.server.listen.config', config):
        max_size, restrict_types, allowed_extensions = load_file_upload_config()

        assert max_size == 10
        assert restrict_types is True
        assert set(allowed_extensions) == {'.txt', '.pdf'}


def test_load_file_upload_config_invalid_max_size():
    config = AppConfig(
        file_uploads_max_file_size_mb=-5,
        file_uploads_restrict_file_types=False,
        file_uploads_allowed_extensions=[],
    )
    with patch('openhands.server.listen.config', config):
        max_size, restrict_types, allowed_extensions = load_file_upload_config()

        assert max_size == 0  # Should default to 0 when invalid
        assert restrict_types is False
        assert allowed_extensions == ['.*']  # Should default to '.*' when empty


def test_is_extension_allowed():
    with patch('openhands.server.listen.RESTRICT_FILE_TYPES', True), patch(
        'openhands.server.listen.ALLOWED_EXTENSIONS', ['.txt', '.pdf']
    ):
        assert is_extension_allowed('file.txt')
        assert is_extension_allowed('file.pdf')
        assert not is_extension_allowed('file.doc')
        assert not is_extension_allowed('file')


def test_is_extension_allowed_no_restrictions():
    with patch('openhands.server.listen.RESTRICT_FILE_TYPES', False):
        assert is_extension_allowed('file.txt')
        assert is_extension_allowed('file.pdf')
        assert is_extension_allowed('file.doc')
        assert is_extension_allowed('file')


def test_is_extension_allowed_wildcard():
    with patch('openhands.server.listen.RESTRICT_FILE_TYPES', True), patch(
        'openhands.server.listen.ALLOWED_EXTENSIONS', ['.*']
    ):
        assert is_extension_allowed('file.txt')
        assert is_extension_allowed('file.pdf')
        assert is_extension_allowed('file.doc')
        assert is_extension_allowed('file')


@pytest.fixture
def test_client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def mock_config():
    """Create a mock config for testing."""
    config = AppConfig(
        sandbox=SandboxConfig(runtime_container_image='test-image'),
        llms={'test': LLMConfig(model='test-model', api_key='test-key')},
    )
    return config


@pytest.fixture
def mock_resolve_issue():
    """Create a mock for resolve_github_issue."""
    with patch('openhands.server.listen.resolve_github_issue') as mock:
        mock.return_value = None
        yield mock


@pytest.fixture
def mock_send_pr():
    """Create a mock for send_github_pr."""
    with patch('openhands.server.listen.send_github_pr') as mock:
        mock.return_value = {'pr_number': 123}
        yield mock


def test_resolve_issue_endpoint(test_client, mock_config, mock_resolve_issue):
    """Test the resolve issue endpoint."""
    with patch('openhands.server.listen.config', mock_config):
        # Test successful resolution
        request_data = {
            'owner': 'test-owner',
            'repo': 'test-repo',
            'token': 'test-token',
            'username': 'test-user',
            'max_iterations': 50,
            'issue_type': 'issue',
            'issue_number': 123,
            'comment_id': None,
        }

        # Create a temp file with test output
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl') as tmp:
            tmp.write('{"test": "data"}\\n')
            tmp.flush()

            # Mock tempfile.mkdtemp to return our temp dir
            with patch('tempfile.mkdtemp', return_value=os.path.dirname(tmp.name)):
                response = test_client.post(
                    '/api/resolver/resolve-issue', json=request_data
                )

        assert response.status_code == 200
        assert response.json()['status'] == 'success'

        # Verify mock was called correctly
        mock_resolve_issue.assert_called_once()
        call_args = mock_resolve_issue.call_args[1]
        assert call_args['owner'] == request_data['owner']
        assert call_args['repo'] == request_data['repo']
        assert call_args['issue_number'] == request_data['issue_number']

        # Test error handling
        mock_resolve_issue.side_effect = Exception('Test error')
        response = test_client.post('/api/resolver/resolve-issue', json=request_data)
        assert response.status_code == 200
        assert response.json()['status'] == 'error'
        assert response.json()['message'] == 'Test error'

        # Test missing output file
        mock_resolve_issue.side_effect = None
        with tempfile.TemporaryDirectory() as tmp_dir:
            with patch('tempfile.mkdtemp', return_value=tmp_dir):
                response = test_client.post(
                    '/api/resolver/resolve-issue', json=request_data
                )
        assert response.status_code == 200
        assert response.json()['status'] == 'error'
        assert response.json()['message'] == 'No output file generated'


def test_send_pull_request_endpoint(test_client, mock_send_pr):
    """Test the send pull request endpoint."""
    request_data = {
        'issue_number': 123,
        'pr_type': 'draft',
        'fork_owner': None,
        'send_on_failure': False,
    }

    # Test successful PR creation
    response = test_client.post('/api/resolver/send-pr', json=request_data)

    assert response.status_code == 200
    assert response.json()['status'] == 'success'
    assert response.json()['result']['pr_number'] == 123

    # Verify mock was called correctly
    mock_send_pr.assert_called_once_with(
        issue_number=123, pr_type='draft', fork_owner=None, send_on_failure=False
    )

    # Test error handling
    mock_send_pr.side_effect = Exception('PR creation failed')
    response = test_client.post('/api/resolver/send-pr', json=request_data)
    assert response.status_code == 200
    assert response.json()['status'] == 'error'
    assert response.json()['message'] == 'PR creation failed'
