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
    assert failed_checks == []  # Changed from 'is None' to '== []'

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

@patch('requests.post')
def test_get_instruction_with_linting_issues(mock_post, pr_handler):
    mock_response = MagicMock()
    mock_response.json.return_value = {
        'data': {
            'repository': {
                'pullRequest': {
                    'mergeable': 'MERGEABLE',
                    'commits': {
                        'nodes': [
                            {
                                'commit': {
                                    'statusCheckRollup': {
                                        'contexts': {
                                            'nodes': [
                                                {
                                                    'name': 'lint',
                                                    'conclusion': 'FAILURE',
                                                    'text': 'ESLint found 2 errors and 1 warning'
                                                }
                                            ]
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
        has_merge_conflicts=False,
        failed_checks=[
            {
                'name': 'lint',
                'description': 'ESLint found 2 errors and 1 warning'
            }
        ]
    )

    template = '{{ pr_status }}'

    instruction, _ = pr_handler.get_instruction(issue, template)

    assert 'This PR has no merge conflicts.' in instruction
    assert 'The following CI checks have failed:' in instruction
    assert 'Linting issues detected.' in instruction
    assert 'lint: ESLint found 2 errors and 1 warning' in instruction
    assert 'Make sure to run the linter locally and address all issues before pushing changes.' in instruction

@patch('requests.post')
def test_get_instruction_with_failed_lint_check(mock_post, pr_handler, capsys):
    # Mocking the response from GitHub API for PR #14
    mock_response = MagicMock()
    mock_response.json.return_value = {
        'data': {
            'repository': {
                'pullRequest': {
                    'mergeable': 'MERGEABLE',
                    'commits': {
                        'nodes': [
                            {
                                'commit': {
                                    'statusCheckRollup': {
                                        'contexts': {
                                            'nodes': [
                                                {
                                                    'name': 'Lint',
                                                    'conclusion': 'FAILURE',
                                                    'text': 'ESLint found issues'
                                                }
                                            ]
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

    # Create a GithubIssue object simulating PR #14
    issue = GithubIssue(
        owner='neubig',
        repo='pr-viewer',
        number=14,
        title='Fix issue #13: Add the option to sort PRs',
        body='This pull request fixes #13.\n\nThe issue has been successfully resolved. The AI implemented a complete sorting functionality for pull requests that addresses the original request.',
        has_merge_conflicts=False,
        failed_checks=[
            {
                'name': 'Lint',
                'description': 'ESLint found issues'
            }
        ]
    )

    template = '{{ pr_status }}'

    instruction, _ = pr_handler.get_instruction(issue, template)

    # Capture the output
    captured = capsys.readouterr()
    print(f"\nGenerated instruction for PR #14:\n{instruction}")

    assert 'This PR has no merge conflicts.' in instruction
    assert 'The following CI checks have failed:' in instruction
    assert 'Lint: ESLint found issues' in instruction
    assert 'Linting issues detected.' in instruction
    assert 'Make sure to run the linter locally and address all issues before pushing changes.' in instruction