import pytest
from unittest.mock import patch, MagicMock

from openhands.resolver.interfaces.github import GithubIssueHandler, GithubPRHandler


@pytest.mark.asyncio
async def test_github_issue_handler_auth_headers():
    """Test that GithubIssueHandler uses Bearer token in authorization headers."""
    # Create a GithubIssueHandler instance
    handler = GithubIssueHandler(
        owner="test-owner",
        repo="test-repo",
        token="test-token",
        username="test-username"
    )
    
    # Check that the headers use Bearer token
    headers = handler.get_headers()
    assert headers["Authorization"] == "Bearer test-token"
    
    # Mock requests.get to check headers in API calls
    with patch("requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        mock_get.return_value = mock_response
        
        # Call a method that uses requests.get
        handler.download_issues()
        
        # Check that the call to requests.get used Bearer token
        call_args = mock_get.call_args
        headers_used = call_args[1]["headers"]
        assert headers_used["Authorization"] == "Bearer test-token"


@pytest.mark.asyncio
async def test_github_pr_handler_auth_headers():
    """Test that GithubPRHandler uses Bearer token in authorization headers."""
    # Create a GithubPRHandler instance
    handler = GithubPRHandler(
        owner="test-owner",
        repo="test-repo",
        token="test-token",
        username="test-username"
    )
    
    # Check that the headers use Bearer token
    headers = handler.get_headers()
    assert headers["Authorization"] == "Bearer test-token"
    
    # Mock requests.post to check headers in GraphQL API calls
    with patch("requests.post") as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": {"repository": {"pullRequest": {}}}}
        mock_post.return_value = mock_response
        
        # Call a method that uses requests.post with GraphQL
        handler.download_pr_metadata(1)
        
        # Check that the call to requests.post used Bearer token
        call_args = mock_post.call_args
        headers_used = call_args[1]["headers"]
        assert headers_used["Authorization"] == "Bearer test-token"