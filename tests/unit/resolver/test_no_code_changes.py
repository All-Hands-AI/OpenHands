import json
from unittest.mock import MagicMock, patch

from openhands.core.config import LLMConfig
from openhands.events.action.message import MessageAction
from openhands.llm import LLM
from openhands.resolver.interfaces.github import GithubIssueHandler, GithubPRHandler
from openhands.resolver.interfaces.issue import Issue
from openhands.resolver.interfaces.issue_definitions import (
    ServiceContextIssue,
    ServiceContextPR,
)


def test_issue_success_without_code_changes():
    """Test that an issue can be marked as successful without code changes."""
    # Mock data
    issue = Issue(
        owner='test',
        repo='test',
        number=1,
        title='Test Issue',
        body='Test body',
        thread_comments=['Please review this solution'],
        review_comments=None,
    )
    history = [MessageAction(content='After reviewing the solution, it looks good and no changes are needed.')]
    llm_config = LLMConfig(model='test', api_key='test')

    # Create a mock response indicating success without code changes
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(
            message=MagicMock(
                content="""--- success
true

--- explanation
The solution has been reviewed and no code changes are needed because:
- The current implementation already handles the case correctly
- The reported issue was a misunderstanding
- No actual bug was found in the code"""
            )
        )
    ]

    # Use patch to mock the LLM completion call
    with patch.object(LLM, 'completion', return_value=mock_response) as mock_completion:
        # Create a handler instance
        handler = ServiceContextIssue(
            GithubIssueHandler('test', 'test', 'test'), llm_config
        )

        # Call guess_success with no git patch
        success, _, explanation = handler.guess_success(issue, history, git_patch=None)

        # Verify the results
        assert success is True
        assert 'The solution has been reviewed' in explanation
        assert 'no code changes are needed' in explanation

        # Verify that LLM completion was called exactly once
        mock_completion.assert_called_once()


def test_pr_success_without_code_changes():
    """Test that a PR can be marked as successful without code changes."""
    # Create a PR handler instance
    llm_config = LLMConfig(model='test', api_key='test')
    handler = ServiceContextPR(GithubPRHandler('test', 'test', 'test'), llm_config)

    # Create a mock issue with thread comments
    issue = Issue(
        owner='test-owner',
        repo='test-repo',
        number=1,
        title='Test PR',
        body='Test Body',
        thread_comments=['Please review this approach'],
        closing_issues=['Issue description'],
        review_comments=None,
        thread_ids=None,
        head_branch='test-branch',
    )

    # Create mock history with a message indicating no changes needed
    history = [MessageAction(content='After reviewing the approach, no code changes are needed because the current implementation is correct.')]

    # Mock the LLM response
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(
            message=MagicMock(
                content="""--- success
true

--- explanation
The review has been completed and no code changes are needed because:
- The current implementation is correct
- The proposed approach would not improve the solution
- The existing code already handles all edge cases"""
            )
        )
    ]

    # Test the guess_success method
    with patch.object(LLM, 'completion', return_value=mock_response):
        success, success_list, explanation = handler.guess_success(issue, history, git_patch=None)

        # Verify the results
        assert success is True
        assert success_list == [True]
        assert 'no code changes are needed' in json.loads(explanation)[0]
