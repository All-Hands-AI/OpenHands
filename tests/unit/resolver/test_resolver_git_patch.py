from unittest.mock import MagicMock

import pytest

from openhands.core.config import LLMConfig
from openhands.events.event import Event
from openhands.events.observation import CmdOutputObservation
from openhands.resolver.github_issue import GithubIssue, ReviewThread
from openhands.resolver.issue_definitions import PRHandler


@pytest.mark.asyncio
async def test_resolver_git_patch_from_event_history():
    """Test that git patches from complete_runtime are properly extracted from event history."""
    # Create test issue
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

    # Create history with a message and a git patch from complete_runtime
    event = Event()
    event._message = 'Made changes to fix the issue'
    cmd_output = CmdOutputObservation(
        command='git diff --no-color --cached HEAD',
        content='diff --git a/test.py b/test.py\n+test line',
        exit_code=0,
        command_id='test-command-1',
    )
    event._observations = [cmd_output]
    history = [event]

    # Call guess_success without git patch - it should be extracted from the event history
    success, success_list, explanation = pr_handler.guess_success(issue, history)

    # Verify the prompt sent to LLM
    prompt = mock_llm.completion.call_args[1]['messages'][0]['content']

    # The git patch should be in the prompt since it was in the event history
    assert 'diff --git' in prompt
    assert '+test line' in prompt
