import os
import tempfile
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from openhands.core.config import AppConfig, LLMConfig, SandboxConfig
from openhands.resolver.github_issue import GithubIssue
from openhands.resolver.resolver_output import ResolverOutput
from openhands.resolver.send_pull_request import ProcessIssueResult


# Mock the SessionManager to avoid asyncio issues
class MockSessionManager:
    def __init__(self, *args, **kwargs):
        pass

    async def attach_to_conversation(self, sid):
        return {'id': sid}

    async def detach_from_conversation(self, conversation):
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
        test_issue = GithubIssue(
            owner='test-owner',
            repo='test-repo',
            number=123,
            title='Test Issue',
            body='Test body',
        )
        test_output = ResolverOutput(
            issue=test_issue,
            issue_type='issue',
            instruction='Test instruction',
            base_commit='abc123',
            git_patch='test patch',
            history=[],
            metrics={},
            success=True,
            success_explanation='Test success',
            error=None,
            comment_success=[],
        )
        mock.return_value = test_output
        yield mock


def test_resolve_issue_endpoint(test_client, mock_config, mock_resolve_issue):
    """Test the resolve issue endpoint."""
    # Create test data using Pydantic models
    test_issue = GithubIssue(
        owner='test-owner',
        repo='test-repo',
        number=123,
        title='Test Issue',
        body='Test body',
    )
    test_output = ResolverOutput(
        issue=test_issue,
        issue_type='issue',
        instruction='Test instruction',
        base_commit='abc123',
        git_patch='test patch',
        history=[],
        metrics={},
        success=True,
        success_explanation='Test success',
        error=None,
        comment_success=[],
    )

    # Set environment variables before creating the test client
    with patch.dict(
        'os.environ', {'GITHUB_TOKEN': 'test-token', 'GITHUB_USERNAME': 'test-user'}
    ):
        with patch('openhands.server.listen.config', mock_config), patch(
            'openhands.server.listen.get_sid_from_token', return_value='test-sid'
        ), patch(
            'openhands.server.listen.create_pull_request_from_resolver_output',
            return_value=ProcessIssueResult(
                success=True, url='https://github.com/test/test/pull/123'
            ),
        ) as mock_send_pr:
            # Test successful resolution and PR creation
            request_data = {
                'owner': 'test-owner',
                'repo': 'test-repo',
                'token': 'test-token',
                'username': 'test-user',
                'max_iterations': 50,
                'issue_type': 'issue',
                'issue_number': 123,
                'comment_id': None,
                'pr_type': 'draft',
                'fork_owner': None,
                'send_on_failure': False,
            }

            # Create a temp directory for our test
            with tempfile.TemporaryDirectory() as test_dir:


                # Mock tempfile.mkdtemp to return our test dir
                with patch('tempfile.mkdtemp', return_value=test_dir):
                    response = test_client.post(
                        '/api/resolver/resolve-issue',
                        json=request_data,
                        headers={'Authorization': 'Bearer test-token'},
                    )

                assert response.status_code == 200
                assert response.json()['status'] == 'success'
                assert (
                    response.json()['result']['url']
                    == 'https://github.com/test/test/pull/123'
                )

                # Verify mocks were called correctly
                mock_resolve_issue.assert_called_once()
                call_args = mock_resolve_issue.call_args[1]
                assert call_args['owner'] == request_data['owner']
                assert call_args['repo'] == request_data['repo']
                assert call_args['issue_number'] == request_data['issue_number']

                mock_send_pr.assert_called_once_with(
                    output_dir=test_dir,
                    resolver_output=test_output,
                    github_token='test-token',
                    github_username='test-user',
                    pr_type='draft',
                    llm_config=mock_config.get_llm_config(),
                    fork_owner=None,
                    send_on_failure=False,
                )

            # Test error handling
            mock_resolve_issue.side_effect = Exception('Test error')
            response = test_client.post(
                '/api/resolver/resolve-issue',
                json=request_data,
                headers={'Authorization': 'Bearer test-token'},
            )
            assert response.status_code == 200
            assert response.json()['status'] == 'error'
            assert response.json()['message'] == 'Test error'

            # Test missing resolver output
            mock_resolve_issue.side_effect = None
            mock_resolve_issue.return_value = None
            response = test_client.post(
                '/api/resolver/resolve-issue',
                json=request_data,
                headers={'Authorization': 'Bearer test-token'},
            )
            assert response.status_code == 200
            assert response.json()['status'] == 'error'
            assert response.json()['message'] == 'No resolver output generated for issue 123'
