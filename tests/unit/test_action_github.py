import os
from opendevin.controller.agent_controller import AgentController
from opendevin.observation.error import AgentErrorObservation
from opendevin.observation.run import CmdOutputObservation
import pytest
from unittest.mock import patch


@pytest.fixture
def agent_controller():
    # Setup the environment variable
    os.environ['OPENDEVIN_GITHUB_TOKEN'] = 'fake_token'
    controller = AgentController()  # Adjust according to your actual instantiation
    yield controller
    # Cleanup the environment variable
    del os.environ['OPENDEVIN_GITHUB_TOKEN']


@pytest.mark.asyncio
@patch('your_module.random.choices')
@patch('your_module.ActionManager.run_command')
async def test_run_successful(mock_run_command, mock_random_choices, agent_controller):
    # Setup mock for random.choices
    mock_random_choices.return_value = ['a', 'b', 'c', 'd', 'e']

    # Create a CmdOutputObservation instance for successful command execution
    successful_output = CmdOutputObservation(exit_code=0)

    # Setup the mock for run_command to return successful output
    mock_run_command.return_value = successful_output

    # Run the method
    result = await agent_controller.run(agent_controller)

    # Verify the result is successful
    assert isinstance(result, CmdOutputObservation)
    assert result.exit_code == 0

    # Verify that the correct remote commands were sent
    expected_calls = [
        (
            'git remote add opendevin_temp_abcde https://fake_token@github.com/owner/repo.git',
            False,
        ),
        ('git push opendevin_temp_remote branch', False),
        ('git remote remove opendevin_temp_abcde', False),
    ]
    mock_run_command.assert_has_calls(expected_calls)


@pytest.mark.asyncio
@patch('your_module.random.choices')
@patch('your_module.ActionManager.run_command')
async def test_run_error_missing_token(
    mock_run_command, mock_random_choices, agent_controller
):
    # Clear the environment variable for this test
    del os.environ['OPENDEVIN_GITHUB_TOKEN']

    # Run the method
    result = await agent_controller.run(agent_controller)

    # Verify the result is an error due to missing token
    assert isinstance(result, AgentErrorObservation)
    assert (
        result.message
        == 'OPENDEVIN_GITHUB_TOKEN is not set in the environment variables'
    )
