"""Tests for the review_pr module."""

import tempfile
from unittest.mock import MagicMock, patch

import pytest

from openhands.core.config import LLMConfig
from openhands.resolver.github_issue import GithubIssue
from openhands.resolver.review_pr import get_pr_diff, post_review_comment, review_pr


@pytest.fixture
def mock_pr() -> GithubIssue:
    """Create a mock PR."""
    return GithubIssue(
        owner='owner',
        repo='repo',
        number=1,
        title='Test PR',
        body='Test PR description',
        thread_comments=None,
        review_comments=None,
    )


@pytest.fixture
def mock_llm_config() -> LLMConfig:
    """Create a mock LLM config."""
    return LLMConfig(
        model='test-model',
        api_key='test-key',
        base_url=None,
    )


def test_get_pr_diff() -> None:
    """Test getting PR diff."""
    with patch('requests.get') as mock_get:
        mock_get.return_value.text = 'test diff'
        diff = get_pr_diff('owner', 'repo', 1, 'token')
        assert diff == 'test diff'
        mock_get.assert_called_once_with(
            'https://api.github.com/repos/owner/repo/pulls/1',
            headers={
                'Authorization': 'token token',
                'Accept': 'application/vnd.github.v3.diff',
            },
        )


def test_post_review_comment() -> None:
    """Test posting review comment."""
    with patch('requests.post') as mock_post:
        post_review_comment('owner', 'repo', 1, 'token', 'test review')
        mock_post.assert_called_once_with(
            'https://api.github.com/repos/owner/repo/issues/1/comments',
            headers={
                'Authorization': 'token token',
                'Accept': 'application/vnd.github.v3+json',
            },
            json={'body': 'test review'},
        )


def test_review_pr(mock_pr: GithubIssue, mock_llm_config: LLMConfig) -> None:
    """Test reviewing PR."""
    with (
        tempfile.TemporaryDirectory() as temp_dir,
        patch('openhands.resolver.review_pr.PRHandler') as mock_handler,
        patch('openhands.resolver.review_pr.get_pr_diff') as mock_get_diff,
        patch('openhands.resolver.review_pr.post_review_comment') as mock_post_comment,
        patch('litellm.completion') as mock_completion,
    ):
        # Setup mocks
        mock_handler.return_value.get_converted_issues.return_value = [mock_pr]
        mock_get_diff.return_value = 'test diff'
        mock_completion.return_value.choices = [
            MagicMock(message=MagicMock(content='test review'))
        ]

        # Run review
        review_pr(
            owner='owner',
            repo='repo',
            token='token',
            username='username',
            output_dir=temp_dir,
            llm_config=mock_llm_config,
            issue_number=1,
        )

        # Verify calls
        mock_handler.assert_called_once_with('owner', 'repo', 'token')
        mock_get_diff.assert_called_once_with('owner', 'repo', 1, 'token')
        mock_completion.assert_called_once()
        mock_post_comment.assert_called_once_with(
            'owner', 'repo', 1, 'token', 'test review'
        )
