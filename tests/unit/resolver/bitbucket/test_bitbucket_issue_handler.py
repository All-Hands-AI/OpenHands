from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from openhands.resolver.interfaces.bitbucket import BitbucketIssueHandler


@pytest.fixture
def bitbucket_handler():
    return BitbucketIssueHandler(
        owner='test-workspace',
        repo='test-repo',
        token='test-token',
        username='test-user',
    )


def test_init():
    handler = BitbucketIssueHandler(
        owner='test-workspace',
        repo='test-repo',
        token='test-token',
        username='test-user',
    )

    assert handler.owner == 'test-workspace'
    assert handler.repo == 'test-repo'
    assert handler.token == 'test-token'
    assert handler.username == 'test-user'
    assert handler.base_domain == 'bitbucket.org'
    assert handler.base_url == 'https://api.bitbucket.org/2.0'
    assert (
        handler.download_url
        == 'https://bitbucket.org/test-workspace/test-repo/get/master.zip'
    )
    assert handler.clone_url == 'https://bitbucket.org/test-workspace/test-repo.git'
    assert handler.headers == {
        'Authorization': 'Bearer test-token',
        'Accept': 'application/json',
    }


def test_get_repo_url(bitbucket_handler):
    assert (
        bitbucket_handler.get_repo_url()
        == 'https://bitbucket.org/test-workspace/test-repo'
    )


def test_get_issue_url(bitbucket_handler):
    assert (
        bitbucket_handler.get_issue_url(123)
        == 'https://bitbucket.org/test-workspace/test-repo/issues/123'
    )


def test_get_pr_url(bitbucket_handler):
    assert (
        bitbucket_handler.get_pr_url(123)
        == 'https://bitbucket.org/test-workspace/test-repo/pull-requests/123'
    )


@pytest.mark.asyncio
@patch('httpx.AsyncClient')
async def test_get_issue(mock_client, bitbucket_handler):
    mock_response = MagicMock()
    mock_response.raise_for_status = AsyncMock()
    mock_response.json.return_value = {
        'id': 123,
        'title': 'Test Issue',
        'content': {'raw': 'Test Issue Body'},
        'links': {
            'html': {
                'href': 'https://bitbucket.org/test-workspace/test-repo/issues/123'
            }
        },
        'state': 'open',
        'reporter': {'display_name': 'Test User'},
        'assignee': [{'display_name': 'Assignee User'}],
    }

    mock_client_instance = AsyncMock()
    mock_client_instance.get.return_value = mock_response
    mock_client.return_value.__aenter__.return_value = mock_client_instance

    issue = await bitbucket_handler.get_issue(123)

    assert issue.number == 123
    assert issue.title == 'Test Issue'
    assert issue.body == 'Test Issue Body'
    # We don't test for html_url, state, user, or assignees as they're not part of the Issue model


@patch('httpx.post')
def test_create_pr(mock_post, bitbucket_handler):
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        'links': {
            'html': {
                'href': 'https://bitbucket.org/test-workspace/test-repo/pull-requests/123'
            }
        },
    }
    mock_post.return_value = mock_response

    pr_url = bitbucket_handler.create_pr(
        title='Test PR',
        body='Test PR Body',
        head='feature-branch',
        base='main',
    )

    assert pr_url == 'https://bitbucket.org/test-workspace/test-repo/pull-requests/123'

    expected_payload = {
        'title': 'Test PR',
        'description': 'Test PR Body',
        'source': {'branch': {'name': 'feature-branch'}},
        'destination': {'branch': {'name': 'main'}},
        'close_source_branch': False,
    }

    mock_post.assert_called_once_with(
        'https://api.bitbucket.org/2.0/repositories/test-workspace/test-repo/pullrequests',
        headers=bitbucket_handler.headers,
        json=expected_payload,
    )
