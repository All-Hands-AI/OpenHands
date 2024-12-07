from unittest.mock import MagicMock, patch

import pytest

from openhands.core.config import LLMConfig
from openhands.resolver.github_issue import GithubIssue
from openhands.resolver.issue_definitions import PRHandler


@pytest.fixture
def pr_handler():
    llm_config = LLMConfig(model='test-model')
    return PRHandler('test-owner', 'test-repo', 'test-token', llm_config)


def test_get_pr_status(pr_handler):
    # Mock the response from GitHub API
    mock_response = MagicMock()
    mock_response.json.return_value = {
        'data': {
            'repository': {
                'pullRequest': {
                    'mergeable': 'CONFLICTING',
                    'commits': {
                        'nodes': [
                            {
                                'commit': {
                                    'statusCheckRollup': {
                                        'contexts': {
                                            'nodes': [
                                                {
                                                    'context': 'test-ci',
                                                    'state': 'FAILURE',
                                                    'description': 'Tests failed',
                                                },
                                                {
                                                    'name': 'build',
                                                    'conclusion': 'FAILURE',
                                                    'text': 'Build failed',
                                                },
                                            ]
                                        }
                                    }
                                }
                            }
                        ]
                    },
                }
            }
        }
    }

    with patch('requests.post', return_value=mock_response):
        has_conflicts, failed_checks = pr_handler._PRHandler__get_pr_status(123)

    assert has_conflicts is True
    assert len(failed_checks) == 2
    assert failed_checks[0] == {'name': 'test-ci', 'description': 'Tests failed'}
    assert failed_checks[1] == {'name': 'build', 'description': 'Build failed'}


def test_get_instruction_with_pr_status(pr_handler):
    # Create a test issue with merge conflicts and failed checks
    issue = GithubIssue(
        owner='test-owner',
        repo='test-repo',
        number=123,
        title='Test PR',
        body='Test body',
        has_merge_conflicts=True,
        failed_checks=[
            {'name': 'test-ci', 'description': 'Tests failed'},
            {'name': 'build', 'description': 'Build failed'},
        ],
    )

    # Test template that includes pr_status
    template = '{{ pr_status }}'

    instruction, _ = pr_handler.get_instruction(issue, template)

    # Verify the instruction includes merge conflict and CI failure info
    assert 'merge conflicts that need to be resolved' in instruction
    assert 'The following CI checks have failed:' in instruction
    assert 'test-ci: Tests failed' in instruction
    assert 'build: Build failed' in instruction
    assert 'examine the GitHub workflow files' in instruction
