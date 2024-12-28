import pytest
from unittest.mock import MagicMock, patch
from openhands.resolver.issue_definitions import PRHandler
from openhands.core.config import LLMConfig
from openhands.resolver.github_issue import GithubIssue

@pytest.fixture
def pr_handler():
    llm_config = LLMConfig(model='test-model')
    return PRHandler('test-owner', 'test-repo', 'test-token', llm_config)

@patch('requests.post')
def test_get_pr_status_pending(mock_post, pr_handler):
    mock_response = MagicMock()
    mock_response.json.return_value = {
        'data': {
            'repository': {
                'pullRequest': {
                    'mergeable': 'UNKNOWN',
                    'commits': {
                        'nodes': [
                            {
                                'commit': {
                                    'statusCheckRollup': {
                                        'contexts': {
                                            'nodes': []
                                        }
                                    }
                                }
                            }
                        ]
                    }
                }
            }
        }
    }
    mock_post.return_value = mock_response

    has_conflicts, failed_checks = pr_handler._PRHandler__get_pr_status(123)

    assert has_conflicts is None
    assert failed_checks is None

@patch('requests.post')
def test_get_instruction_pending_status(mock_post, pr_handler):
    mock_response = MagicMock()
    mock_response.json.return_value = {
        'data': {
            'repository': {
                'pullRequest': {
                    'mergeable': 'UNKNOWN',
                    'commits': {
                        'nodes': [
                            {
                                'commit': {
                                    'statusCheckRollup': {
                                        'contexts': {
                                            'nodes': []
                                        }
                                    }
                                }
                            }
                        ]
                    }
                }
            }
        }
    }
    mock_post.return_value = mock_response

    issue = GithubIssue(
        owner='test-owner',
        repo='test-repo',
        number=123,
        title='Test PR',
        body='Test body',
        has_merge_conflicts=None,
        failed_checks=None
    )

    template = '{{ pr_status }}'

    instruction, _ = pr_handler.get_instruction(issue, template)

    assert 'The merge status of this PR is currently unknown or pending.' in instruction
    assert 'The CI check status is currently unknown or pending.' in instruction