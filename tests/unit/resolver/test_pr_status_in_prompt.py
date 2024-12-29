from unittest.mock import MagicMock, patch

from openhands.core.config import LLMConfig
from openhands.resolver.github_issue import GithubIssue
from openhands.resolver.issue_definitions import PRHandler


@patch('requests.post')
def test_pr_status_in_basic_followup_template(mock_post):
    """Test that PR status is included in the basic-followup template."""
    # Mock the GitHub API response for PR status
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
                                                    'text': 'ESLint found issues',
                                                }
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
    mock_post.return_value = mock_response

    # Create a PR handler instance
    llm_config = LLMConfig(model='test-model')
    handler = PRHandler('test-owner', 'test-repo', 'test-token', llm_config)

    # Create a mock issue
    issue = GithubIssue(
        owner='test-owner',
        repo='test-repo',
        number=123,
        title='Test PR',
        body='Test body',
        has_merge_conflicts=False,
        failed_checks=[{'name': 'lint', 'description': 'ESLint found issues'}],
    )

    # Use the basic-followup template
    with open('openhands/resolver/prompts/resolve/basic-followup.jinja', 'r') as f:
        template = f.read()

    # Generate instruction
    instruction, _ = handler.get_instruction(issue, template)

    # Check that PR status information is included
    assert 'The following CI checks have failed:' in instruction
    assert 'lint: ESLint found issues' in instruction
    assert 'Please examine the GitHub workflow files' in instruction
    assert 'Please run the failing checks locally to fix the issues.' in instruction


@patch('requests.post')
def test_pr_status_in_custom_template(mock_post):
    """Test that PR status is included when using a custom template."""
    # Mock the GitHub API response for PR status
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
                                                    'text': 'ESLint found issues',
                                                }
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
    mock_post.return_value = mock_response

    # Create a PR handler instance
    llm_config = LLMConfig(model='test-model')
    handler = PRHandler('test-owner', 'test-repo', 'test-token', llm_config)

    # Create a mock issue
    issue = GithubIssue(
        owner='test-owner',
        repo='test-repo',
        number=123,
        title='Test PR',
        body='Test body',
        has_merge_conflicts=False,
        failed_checks=[{'name': 'lint', 'description': 'ESLint found issues'}],
    )

    # Use a custom template that includes pr_status
    template = """
    # PR Status
    {{ pr_status }}

    # Problem Statement
    {{ body }}
    """

    # Generate instruction
    instruction, _ = handler.get_instruction(issue, template)

    # Check that PR status information is included
    assert 'The following CI checks have failed:' in instruction
    assert 'lint: ESLint found issues' in instruction
    assert 'Please examine the GitHub workflow files' in instruction
    assert 'Please run the failing checks locally to fix the issues.' in instruction
