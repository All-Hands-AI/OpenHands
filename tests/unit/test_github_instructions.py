from unittest.mock import MagicMock, patch

import pytest

from openhands.server.routes.instructions import (
    add_permanent_microagent,
    create_instructions_pr,
    get_repo_instructions,
    get_repo_microagents,
)

MOCK_REPO = 'test-org/test-repo'
MOCK_TOKEN = 'mock-token'
MOCK_BRANCH = 'mock-branch'
MOCK_SHA = 'mock-sha'
MOCK_PR_URL = 'https://github.com/test-org/test-repo/pull/1'


@pytest.fixture
def mock_env(monkeypatch):
    monkeypatch.setenv('GITHUB_TOKEN', MOCK_TOKEN)


@pytest.fixture
def mock_github_api():
    with patch('openhands.server.routes.instructions.requests') as mock_requests:
        mock_requests.get = MagicMock()
        mock_requests.post = MagicMock()
        mock_requests.put = MagicMock()
        yield mock_requests


def test_get_repo_instructions_success(mock_env, mock_github_api):
    # Mock the response for getting instructions file
    mock_github_api.get.return_value.status_code = 200
    mock_github_api.get.return_value.json.return_value = {
        'content': 'IyBUZXN0IEluc3RydWN0aW9ucw==',  # base64 for "# Test Instructions"
        'html_url': 'https://github.com/test-org/test-repo/blob/main/.openhands_instructions',
    }

    result = get_repo_instructions(MOCK_REPO)

    # Verify API call
    mock_github_api.get.assert_called_once_with(
        f'https://api.github.com/repos/{MOCK_REPO}/contents/.openhands_instructions',
        headers={'Authorization': f'Bearer {MOCK_TOKEN}'},
    )

    # Verify result
    assert result['hasInstructions'] is True
    assert result['instructions'] == '# Test Instructions'
    assert 'tutorialUrl' in result


def test_create_instructions_pr_success(mock_env, mock_github_api):
    # Mock responses for each API call
    mock_github_api.get.return_value.json.return_value = {'object': {'sha': MOCK_SHA}}
    mock_github_api.post.return_value.status_code = 201
    mock_github_api.post.return_value.json.return_value = {'html_url': MOCK_PR_URL}
    mock_github_api.put.return_value.status_code = 201

    result = create_instructions_pr(MOCK_REPO, '# New Instructions')

    # Verify API calls sequence
    assert mock_github_api.get.call_count == 1  # Get main branch SHA
    assert mock_github_api.post.call_count == 2  # Create branch + Create PR
    assert mock_github_api.put.call_count == 1  # Create/update file

    # Verify result
    assert result['success'] is True
    assert result['pullRequestUrl'] == MOCK_PR_URL


def test_get_repo_microagents_with_agents(mock_env, mock_github_api):
    # Mock response for getting repo tree
    mock_github_api.get.return_value.status_code = 200
    mock_github_api.get.return_value.json.return_value = {
        'tree': [
            {'path': '.openhands/microagents/test-agent.md', 'type': 'blob'},
            {'path': '.openhands/microagents/another-agent.md', 'type': 'blob'},
            {'path': 'some/other/file.txt', 'type': 'blob'},
        ]
    }

    result = get_repo_microagents(MOCK_REPO)

    # Verify API call
    mock_github_api.get.assert_called_once_with(
        f'https://api.github.com/repos/{MOCK_REPO}/git/trees/main?recursive=1',
        headers={'Authorization': f'Bearer {MOCK_TOKEN}'},
    )

    # Verify result
    assert len(result) == 2
    assert all(agent['isPermanent'] for agent in result)
    assert {'test-agent', 'another-agent'} == {agent['name'] for agent in result}


def test_add_permanent_microagent_success(mock_env, mock_github_api):
    # Mock responses for each API call
    mock_github_api.get.return_value.json.return_value = {'object': {'sha': MOCK_SHA}}
    mock_github_api.post.return_value.status_code = 201
    mock_github_api.put.return_value.status_code = 201

    result = add_permanent_microagent(MOCK_REPO, '# New Agent Instructions')

    # Verify API calls sequence
    assert mock_github_api.get.call_count == 1  # Get main branch SHA
    assert mock_github_api.post.call_count == 2  # Create branch + Create PR
    assert mock_github_api.put.call_count == 1  # Create agent file

    # Verify result
    assert result['success'] is True
    assert 'agentId' in result


def test_error_handling(mock_env, mock_github_api):
    # Test error when getting instructions
    mock_github_api.get.return_value.status_code = 404
    result = get_repo_instructions(MOCK_REPO)
    assert result['hasInstructions'] is False

    # Test error when creating PR
    mock_github_api.post.return_value.status_code = 422
    result = create_instructions_pr(MOCK_REPO, '# Test')
    assert result['success'] is False

    # Test error when getting microagents
    mock_github_api.get.return_value.status_code = 404
    result = get_repo_microagents(MOCK_REPO)
    assert len(result) == 0


def test_branch_name_format(mock_env, mock_github_api):
    # Mock successful responses
    mock_github_api.get.return_value.json.return_value = {'object': {'sha': MOCK_SHA}}
    mock_github_api.post.return_value.status_code = 201
    mock_github_api.put.return_value.status_code = 201

    # Test instructions PR branch name
    create_instructions_pr(MOCK_REPO, '# Test')
    branch_call = mock_github_api.post.call_args_list[0]
    branch_data = branch_call[1]['json']
    assert branch_data['ref'].startswith('refs/heads/add-instructions-')
    assert len(branch_data['ref']) > 30  # Ensure UUID is added

    # Test microagent PR branch name
    mock_github_api.post.reset_mock()
    add_permanent_microagent(MOCK_REPO, '# Test')
    branch_call = mock_github_api.post.call_args_list[0]
    branch_data = branch_call[1]['json']
    assert branch_data['ref'].startswith('refs/heads/add-microagent-')
    assert len(branch_data['ref']) > 30  # Ensure UUID is added
