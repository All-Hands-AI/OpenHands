from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from openhands.resolver.interfaces.bitbucket import BitbucketIssueHandler
from openhands.resolver.send_pull_request import send_pull_request


@pytest.mark.asyncio
@patch('openhands.resolver.send_pull_request.get_issue_handler')
async def test_send_pull_request_bitbucket(mock_get_issue_handler):
    # Mock the BitbucketIssueHandler
    mock_handler = MagicMock(spec=BitbucketIssueHandler)
    mock_handler.create_pr = AsyncMock(
        return_value='https://bitbucket.org/test-workspace/test-repo/pull-requests/123'
    )
    mock_get_issue_handler.return_value = mock_handler

    # Call send_pull_request
    result = await send_pull_request(
        provider='bitbucket',
        owner='test-workspace',
        repo='test-repo',
        title='Test PR',
        body='Test PR Body',
        head='feature-branch',
        base='main',
        token='test-token',
    )

    # Verify the result
    assert result == 'https://bitbucket.org/test-workspace/test-repo/pull-requests/123'

    # Verify the handler was created correctly
    mock_get_issue_handler.assert_called_once_with(
        'bitbucket',
        'test-workspace',
        'test-repo',
        'test-token',
        None,
        None,
    )

    # Verify create_pr was called correctly
    mock_handler.create_pr.assert_called_once_with(
        title='Test PR',
        body='Test PR Body',
        head='feature-branch',
        base='main',
    )
