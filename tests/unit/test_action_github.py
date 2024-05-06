from unittest.mock import MagicMock, call, patch

import pytest

from agenthub.dummy_agent.agent import DummyAgent
from opendevin.controller.agent_controller import AgentController
from opendevin.core import config
from opendevin.core.schema.config import ConfigType
from opendevin.events.action.github import GitHubPushAction, GitHubSendPRAction
from opendevin.events.observation.commands import CmdOutputObservation
from opendevin.events.observation.error import AgentErrorObservation
from opendevin.events.observation.message import AgentMessageObservation
from opendevin.events.stream import EventStream
from opendevin.llm.llm import LLM


@pytest.fixture
def agent_controller():
    # Setup the environment variable
    config.config[ConfigType.SANDBOX_TYPE] = 'local'
    llm = LLM()
    agent = DummyAgent(llm=llm)
    event_stream = EventStream()
    controller = AgentController(agent, event_stream)
    yield controller


@pytest.mark.asyncio
@patch.dict(config.config, {'GITHUB_TOKEN': 'fake_token'}, clear=True)
@patch('random.choices')
@patch('opendevin.controller.action_manager.ActionManager.run_command')
async def test_run_push_successful(
    mock_run_command, mock_random_choices, agent_controller
):
    # Setup mock for random.choices
    mock_random_choices.return_value = ['a', 'b', 'c', 'd', 'e']

    # Create a CmdOutputObservation instance for successful command execution
    successful_output = CmdOutputObservation(
        content='', command_id=1, command='', exit_code=0
    )

    # Setup the mock for run_command to return successful output
    mock_run_command.return_value = successful_output

    # Run the method
    push_action = GitHubPushAction(owner='owner', repo='repo', branch='branch')
    result = await push_action.run(agent_controller)

    # Verify the result is successful
    assert isinstance(result, CmdOutputObservation)
    assert result.exit_code == 0

    # Verify that the correct remote commands were sent
    expected_calls = [
        call(
            'git remote add opendevin_temp_abcde https://fake_token@github.com/owner/repo.git',
            background=False,
        ),
        call('git push opendevin_temp_abcde branch', background=False),
        call('git remote remove opendevin_temp_abcde', background=False),
    ]
    mock_run_command.assert_has_calls(expected_calls)


@pytest.mark.asyncio
@patch('random.choices')
@patch('opendevin.controller.action_manager.ActionManager.run_command')
async def test_run_push_error_missing_token(
    mock_run_command, mock_random_choices, agent_controller
):
    # Run the method
    push_action = GitHubPushAction(owner='owner', repo='repo', branch='branch')
    result = await push_action.run(agent_controller)

    # Verify the result is an error due to missing token
    assert isinstance(result, AgentErrorObservation)
    assert result.message == 'Oops. Something went wrong: GITHUB_TOKEN is not set'


@pytest.mark.asyncio
@patch.dict(config.config, {'GITHUB_TOKEN': 'fake_token'}, clear=True)
@patch('requests.post')
async def test_run_pull_request_created_successfully(mock_post, agent_controller):
    # Set up the mock for the requests.post call to simulate a successful pull request creation
    mock_response = MagicMock()
    mock_response.status_code = 201
    mock_response.json.return_value = {'html_url': 'https://github.com/example/pull/1'}
    mock_post.return_value = mock_response

    # Run the method
    pr_action = GitHubSendPRAction(
        owner='owner',
        repo='repo',
        title='title',
        head='head',
        head_repo='head_repo',
        base='base',
        body='body',
    )
    result = await pr_action.run(agent_controller)

    # Verify the result is a success observation
    assert isinstance(result, AgentMessageObservation)
    assert 'Pull request created successfully' in result.content
    assert 'https://github.com/example/pull/1' in result.content


@pytest.mark.asyncio
@patch('requests.post')
@patch.dict(config.config, {'GITHUB_TOKEN': 'fake_token'}, clear=True)
async def test_run_pull_request_creation_failed(mock_post, agent_controller):
    # Set up the mock for the requests.post call to simulate a failed pull request creation
    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.text = 'Bad Request'
    mock_post.return_value = mock_response

    # Run the method
    pr_action = GitHubSendPRAction(
        owner='owner',
        repo='repo',
        title='title',
        head='head',
        head_repo='head_repo',
        base='base',
        body='body',
    )
    result = await pr_action.run(agent_controller)

    # Verify the result is an error observation
    assert isinstance(result, AgentErrorObservation)
    assert 'Failed to create pull request' in result.content
    assert 'Status code: 400' in result.content
    assert 'Bad Request' in result.content


@pytest.mark.asyncio
async def test_run_error_missing_token(agent_controller):
    # Run the method
    pr_action = GitHubSendPRAction(
        owner='owner',
        repo='repo',
        title='title',
        head='head',
        head_repo='head_repo',
        base='base',
        body='body',
    )
    result = await pr_action.run(agent_controller)

    # Verify the result is an error due to missing token
    assert isinstance(result, AgentErrorObservation)
    assert 'GITHUB_TOKEN is not set' in result.message
