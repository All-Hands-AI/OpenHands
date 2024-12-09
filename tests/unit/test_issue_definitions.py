from unittest.mock import Mock, patch

import pytest

from openhands.core.config import LLMConfig
from openhands.resolver.issue_definitions import PRHandler


@pytest.fixture
def pr_handler():
    return PRHandler(
        owner='test-owner',
        repo='test-repo',
        token='test-token',
        llm_config=LLMConfig(model='test-model'),
    )


def test_get_converted_issues_fetches_specific_issues(pr_handler):
    # Mock responses for each API call
    issue_response = Mock()
    issue_response.json.return_value = {
        'number': 123,
        'title': 'Test Issue',
        'body': 'Test body',
        'state': 'open',
        'head': {'ref': 'test-branch'},
        'pull_request': {
            'url': 'https://github.com/test-owner/test-repo/pull/123'
        },  # This makes it a PR
    }

    graphql_response = Mock()
    graphql_response.json.return_value = {
        'data': {
            'repository': {
                'pullRequest': {
                    'closingIssuesReferences': {'edges': []},
                    'url': 'https://github.com/test-owner/test-repo/pull/123',
                    'reviews': {'nodes': []},
                    'reviewThreads': {'edges': []},
                }
            }
        }
    }

    comments_response = Mock()
    comments_response.json.return_value = []

    # Set up the mock for requests.get and requests.post
    with patch('requests.get') as mock_get, patch('requests.post') as mock_post:
        mock_get.side_effect = [issue_response, comments_response]
        mock_post.return_value = graphql_response

        # Test fetching a specific issue
        issues = pr_handler.get_converted_issues(issue_numbers=[123])

        # Verify the results
        assert len(issues) == 1
        assert issues[0].number == 123
        assert issues[0].title == 'Test Issue'

        # Verify API calls
        assert mock_get.call_count == 2  # One for issue, one for comments
        assert mock_post.call_count == 1  # One for GraphQL metadata

        # Verify the URLs called
        issue_url = 'https://api.github.com/repos/test-owner/test-repo/issues/123'
        comments_url = (
            'https://api.github.com/repos/test-owner/test-repo/issues/123/comments'
        )
        graphql_url = 'https://api.github.com/graphql'

        mock_get.assert_any_call(
            issue_url,
            headers={
                'Authorization': 'token test-token',
                'Accept': 'application/vnd.github.v3+json',
            },
        )
        mock_get.assert_any_call(
            comments_url,
            headers={
                'Authorization': 'token test-token',
                'Accept': 'application/vnd.github.v3+json',
            },
            params={'per_page': 100, 'page': 1},
        )
        mock_post.assert_called_once_with(
            graphql_url,
            json={
                'query': mock_post.call_args[1]['json'][
                    'query'
                ],  # Query is too long to compare directly
                'variables': {'owner': 'test-owner', 'repo': 'test-repo', 'pr': 123},
            },
            headers={
                'Authorization': 'Bearer test-token',
                'Content-Type': 'application/json',
            },
        )
