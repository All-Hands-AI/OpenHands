from unittest.mock import MagicMock

import pytest

from openhands.core.config import LLMConfig
from openhands.events.event import Event
from openhands.resolver.github_issue import GithubIssue, ReviewThread
from openhands.resolver.issue_definitions import PRHandler


@pytest.fixture
def pr_handler():
    llm_config = LLMConfig(model='test-model')
    return PRHandler('test-owner', 'test-repo', 'test-token', llm_config)


@pytest.fixture
def mock_llm_response():
    return MagicMock(
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


def test_guess_success_includes_git_patch(pr_handler, mock_llm_response):
    # Mock the issue
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

    # Mock the history with git patch
    event1 = Event()
    event1._message = 'Initial message'
    event1.metrics = {'some_metric': 'value'}

    event2 = Event()
    event2._message = 'Final message'
    event2.metrics = {'git_patch': 'diff --git a/test.py b/test.py\n+test line'}

    history = [event1, event2]

    # Mock the LLM class
    mock_llm = MagicMock()
    mock_llm.completion.return_value = mock_llm_response
    pr_handler.llm = mock_llm
    success, success_list, explanation = pr_handler.guess_success(issue, history)

    # Verify that git patch was included in the prompt
    assert mock_llm.completion.call_count == 1
    prompt = mock_llm.completion.call_args[1]['messages'][0]['content']
    assert 'diff --git a/test.py b/test.py' in prompt
    assert '+test line' in prompt


def test_guess_success_includes_git_patch_from_command_output(
    pr_handler, mock_llm_response
):
    # Mock the issue
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

    # Mock the history with git patch in command output
    event1 = Event()
    event1._message = 'Initial message'
    event1.metrics = {'some_metric': 'value'}

    event2 = Event()
    event2._message = 'Final message'
    event2.content = 'diff --git a/test.py b/test.py\n+test line'

    history = [event1, event2]

    # Mock the LLM class
    mock_llm = MagicMock()
    mock_llm.completion.return_value = mock_llm_response
    pr_handler.llm = mock_llm
    success, success_list, explanation = pr_handler.guess_success(issue, history)

    # Verify that git patch was included in the prompt
    assert mock_llm.completion.call_count == 1
    prompt = mock_llm.completion.call_args[1]['messages'][0]['content']
    assert 'diff --git a/test.py b/test.py' in prompt
    assert '+test line' in prompt


def test_guess_success_handles_missing_git_patch(pr_handler, mock_llm_response):
    # Mock the issue
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

    # Mock the history without git patch
    event1 = Event()
    event1._message = 'Initial message'
    event1.metrics = {'some_metric': 'value'}

    event2 = Event()
    event2._message = 'Final message'
    event2.metrics = {'other_metric': 'value'}

    history = [event1, event2]

    # Mock the LLM class
    mock_llm = MagicMock()
    mock_llm.completion.return_value = mock_llm_response
    pr_handler.llm = mock_llm
    success, success_list, explanation = pr_handler.guess_success(issue, history)

    # Verify that "No changes made yet" was included in the prompt
    assert mock_llm.completion.call_count == 1
    prompt = mock_llm.completion.call_args[1]['messages'][0]['content']
    assert 'No changes made yet' in prompt
