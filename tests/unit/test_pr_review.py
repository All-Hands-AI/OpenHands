import os
from unittest.mock import MagicMock, patch

import pytest

from openhands.core.config import LLMConfig
from openhands.resolver.github_issue import GithubIssue, ReviewThread
from openhands.resolver.issue_definitions import PRHandler


@pytest.fixture
def pr_handler():
    return PRHandler('test-owner', 'test-repo', 'test-token')


@pytest.fixture
def test_pr():
    return GithubIssue(
        owner='test-owner',
        repo='test-repo',
        number=1,
        title='Test PR',
        body='This is a test PR with some changes.',
        thread_comments=['LGTM!'],
        review_comments=['Please fix this issue.'],
        review_threads=[
            ReviewThread(
                comment='Fix this code style issue',
                files=['src/main.py'],
            )
        ],
        head_branch='feature-branch',
    )


@pytest.fixture
def llm_config():
    return LLMConfig(
        model='test-model',
        api_key='test-key',
        base_url='test-url',
    )


def test_pr_review_instruction(pr_handler, test_pr):
    with patch('jinja2.Template') as mock_template:
        mock_template.return_value.render.return_value = 'Test instruction'
        instruction, images = pr_handler.get_instruction(
            test_pr,
            'pr-review',
            repo_instruction='Test repo instruction',
        )
        assert instruction == 'Test instruction'
        assert images == []
        mock_template.return_value.render.assert_called_once_with(
            body='Test PR\n\nThis is a test PR with some changes.\n\nIssue Thread Comments:\nLGTM!\n\nReview Comments:\nPlease fix this issue.\n\nReview Threads:\nFile: src/main.py\nFix this code style issue',
            repo_instruction='Test repo instruction',
        )


def test_pr_review_success_guess(pr_handler, test_pr, llm_config):
    with patch('litellm.completion') as mock_completion:
        mock_completion.return_value.choices = [
            MagicMock(message=MagicMock(content='--- success\ntrue\n--- explanation\nAll issues fixed.'))
        ]
        success, comment_success, explanation = pr_handler.guess_success(
            test_pr,
            [MagicMock(message='Fixed all issues.')],
            llm_config,
        )
        assert success is True
        assert comment_success is None
        assert explanation == 'All issues fixed.'
        mock_completion.assert_called_once_with(
            model='test-model',
            messages=[{'role': 'user', 'content': mock_completion.call_args[1]['messages'][0]['content']}],
            api_key='test-key',
            base_url='test-url',
        )
