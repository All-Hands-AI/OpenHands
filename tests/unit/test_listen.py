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


def test_send_pull_request_endpoint(test_client, mock_config):
    """Test the send pull request endpoint."""
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
    with patch.dict('os.environ', {'GITHUB_TOKEN': 'test-token', 'GITHUB_USERNAME': 'test-user'}):
        with patch('openhands.server.listen.config', mock_config), patch(
            'openhands.server.listen.get_sid_from_token', return_value='test-sid'
        ), patch(
            'openhands.resolver.io_utils.load_single_resolver_output',
            return_value=test_output,
        ), patch(
            'openhands.server.listen.process_single_issue',
            return_value=ProcessIssueResult(
                success=True, url='https://github.com/test/test/pull/123'
            ),
        ) as mock_send_pr:
            request_data = {
                'issue_number': 123,
                'pr_type': 'draft',
                'fork_owner': None,
                'send_on_failure': False,
            }

            # Create a temp directory for our test
            with tempfile.TemporaryDirectory() as test_dir:
                # Create the openhands_resolver directory
                output_dir = os.path.join(test_dir, 'openhands_resolver')
                os.makedirs(output_dir)

                # Create a temp file with test output
                output_file = os.path.join(output_dir, 'output.jsonl')
                with open(output_file, 'w') as tmp:
                    tmp.write('{"issue": {"owner": "test-owner", "repo": "test-repo", "number": 123, "title": "Test Issue", "body": "Test body"}, "issue_type": "issue", "instruction": "Test instruction", "base_commit": "abc123", "git_patch": "test patch", "history": [], "metrics": {}, "success": true, "success_explanation": "Test success", "error": null, "comment_success": []}\n')

                # Mock tempfile.gettempdir to return our test dir
                with patch('tempfile.gettempdir', return_value=test_dir):
                    # Test successful PR creation
                    response = test_client.post(
                        '/api/resolver/send-pr',
                        json=request_data,
                        headers={'Authorization': 'Bearer test-token'},
                    )

                    assert response.status_code == 200
                    assert response.json()['status'] == 'success'
                    assert (
                        response.json()['result']['url']
                        == 'https://github.com/test/test/pull/123'
                    )

                    # Verify mock was called correctly
                    mock_send_pr.assert_called_once_with(
                        output_dir=output_dir,
                        resolver_output=test_output,
                        github_token='test-token',
                        github_username='test-user',
                        pr_type='draft',
                        llm_config=mock_config.get_llm_config(),
                        fork_owner=None,
                        send_on_failure=False,
                    )

                    # Test error handling
                    mock_send_pr.side_effect = Exception('PR creation failed')
                    response = test_client.post(
                        '/api/resolver/send-pr',
                        json=request_data,
                        headers={'Authorization': 'Bearer test-token'},
                    )
                    assert response.status_code == 200
                    assert response.json()['status'] == 'error'
                    assert response.json()['message'] == 'PR creation failed'