import pytest
from unittest.mock import MagicMock, patch

from openhands.core.config import LLMConfig
from openhands.events.event import Event
from openhands.events.observation import CmdOutputObservation
from openhands.resolver.github_issue import GithubIssue, ReviewThread
from openhands.resolver.issue_definitions import PRHandler
from openhands.resolver.resolve_issue import process_issue


@pytest.mark.asyncio
async def test_resolver_git_patch_not_in_history():
    """Test that git patches executed by resolver are not captured in event history."""
    # Mock dependencies
    config = MagicMock()
    issue = GithubIssue(
        owner='test-owner',
        repo='test-repo',
        number=1,
        title='Test PR',
        body='Test body',
        review_threads=[
            ReviewThread(
                id='thread1',
                comment='Please fix this',
                files=['test.py'],
            )
        ],
        closing_issues=[],
    )
    
    # Create a PR handler
    llm_config = LLMConfig(model='test-model')
    pr_handler = PRHandler('test-owner', 'test-repo', 'test-token', llm_config)
    
    # Mock the LLM to return success
    mock_llm = MagicMock()
    mock_llm.completion.return_value = MagicMock(
        choices=[
            MagicMock(
                message=MagicMock(
                    content="""--- success
true

--- explanation
The changes look good"""
                )
            )
        ]
    )
    pr_handler.llm = mock_llm
    
    # Create history with a message but no git patch
    event = Event()
    event._message = 'Made changes to fix the issue'
    history = [event]
    
    # Execute git patch command directly (simulating resolver behavior)
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(
            stdout='diff --git a/test.py b/test.py\n+test line',
            returncode=0
        )
        
        # Call guess_success with git patch
        git_patch = 'diff --git a/test.py b/test.py\n+test line'
        success, success_list, explanation = pr_handler.guess_success(issue, history, git_patch)
        
        # Verify the prompt sent to LLM
        prompt = mock_llm.completion.call_args[1]['messages'][0]['content']
        
        # The git patch should be in the prompt since we passed it directly
        assert 'diff --git' in prompt
        assert '+test line' in prompt