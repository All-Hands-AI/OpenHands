import os
import pytest
from openhands.resolver.issue_definitions import IssueHandler
from openhands.resolver.github_issue import GithubIssue
from openhands.events.event import Event
from openhands.core.config import LLMConfig

@pytest.fixture
def issue_handler():
    return IssueHandler(
        owner="test-owner",
        repo="test-repo",
        token="test-token",
        llm_config=LLMConfig(model="gpt-4", api_key="test-key")
    )

def test_guess_success_with_patch_content(issue_handler, mocker):
    # Mock the issue
    issue = GithubIssue(
        owner="test-owner",
        repo="test-repo",
        number=1,
        title="Test Issue",
        body="Fix the bug in the code",
        thread_comments=None,
        review_comments=None
    )
    
    # Mock the history with patch content
    event = Event()
    event._message = "All done! I've fixed the issue by making the following changes:\n\nPatch content:\n```diff\n--- a/src/file.py\n+++ b/src/file.py\n@@ -10,7 +10,7 @@\n-    buggy_code()\n+    fixed_code()\n```"
    history = [event]
    
    # Mock LLM response
    mock_response = mocker.MagicMock()
    mock_response.choices = [
        mocker.MagicMock(
            message=mocker.MagicMock(
                content="""--- success
true
--- explanation
The issue has been resolved. The patch shows that the buggy code was replaced with fixed code."""
            )
        )
    ]
    mocker.patch.object(issue_handler.llm, '_completion', return_value=mock_response)
    
    # Test the function
    success, _, explanation = issue_handler.guess_success(issue, history)
    assert success is True
    assert "patch shows" in explanation.lower()

def test_guess_success_without_patch_content(issue_handler, mocker):
    # Mock the issue
    issue = GithubIssue(
        owner="test-owner",
        repo="test-repo",
        number=1,
        title="Test Issue",
        body="Fix the bug in the code",
        thread_comments=None,
        review_comments=None
    )
    
    # Mock the history without patch content
    event = Event()
    event._message = "All done!"
    history = [event]
    
    # Mock LLM response
    mock_response = mocker.MagicMock()
    mock_response.choices = [
        mocker.MagicMock(
            message=mocker.MagicMock(
                content="""--- success
false
--- explanation
Cannot verify the resolution as no patch content is provided."""
            )
        )
    ]
    mocker.patch.object(issue_handler.llm, '_completion', return_value=mock_response)
    
    # Test the function
    success, _, explanation = issue_handler.guess_success(issue, history)
    assert success is False
    assert "no patch content" in explanation.lower()
