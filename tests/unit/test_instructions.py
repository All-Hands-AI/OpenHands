from unittest.mock import patch

import pytest

from openhands.server.routes.instructions import (
    add_permanent_microagent,
    add_temporary_microagent,
    create_instructions_pr,
    get_repo_instructions,
    get_repo_microagents,
)


@pytest.fixture
def mock_github_api():
    with (
        patch('openhands.server.routes.instructions.requests.get') as mock_get,
        patch('openhands.server.routes.instructions.requests.post') as mock_post,
    ):
        yield {'get': mock_get, 'post': mock_post}


def test_get_repo_instructions_exists(mock_github_api):
    mock_github_api['get'].return_value.status_code = 200
    mock_github_api['get'].return_value.json.return_value = {
        'content': 'IyBPcGVuSGFuZHMgSW5zdHJ1Y3Rpb25zCgpUaGlzIGlzIGEgdGVzdC4=',  # base64 encoded
        'html_url': 'https://github.com/test/repo/blob/main/.openhands_instructions',
    }

    result = get_repo_instructions('test/repo')
    assert result['hasInstructions'] is True
    assert result['instructions'] == '# OpenHands Instructions\n\nThis is a test.'
    assert (
        result['tutorialUrl']
        == 'https://github.com/test/repo/blob/main/.openhands_instructions'
    )


def test_get_repo_instructions_not_exists(mock_github_api):
    mock_github_api['get'].return_value.status_code = 404

    result = get_repo_instructions('test/repo')
    assert result['hasInstructions'] is False
    assert result['instructions'] == ''
    assert result['tutorialUrl'] == ''


def test_create_instructions_pr(mock_github_api):
    mock_github_api['post'].return_value.status_code = 201
    mock_github_api['post'].return_value.json.return_value = {
        'html_url': 'https://github.com/test/repo/pull/1'
    }

    result = create_instructions_pr('test/repo', '# Test Instructions')
    assert result['success'] is True
    assert result['pullRequestUrl'] == 'https://github.com/test/repo/pull/1'


def test_get_repo_microagents_exists(mock_github_api):
    mock_github_api['get'].return_value.status_code = 200
    mock_github_api['get'].return_value.json.return_value = {
        'tree': [
            {'path': '.openhands/microagents/test.md', 'type': 'blob'},
            {'path': '.openhands/microagents/other.md', 'type': 'blob'},
        ]
    }

    result = get_repo_microagents('test/repo')
    assert len(result) == 2
    assert result[0]['name'] == 'test'
    assert result[1]['name'] == 'other'


def test_get_repo_microagents_not_exists(mock_github_api):
    mock_github_api['get'].return_value.status_code = 404

    result = get_repo_microagents('test/repo')
    assert len(result) == 0


def test_add_temporary_microagent():
    result = add_temporary_microagent('test/repo', '# Test Instructions')
    assert result['success'] is True
    assert 'agentId' in result


def test_add_permanent_microagent(mock_github_api):
    mock_github_api['post'].return_value.status_code = 201
    mock_github_api['post'].return_value.json.return_value = {
        'html_url': 'https://github.com/test/repo/pull/1'
    }

    result = add_permanent_microagent('test/repo', '# Test Instructions')
    assert result['success'] is True
    assert 'agentId' in result
