from agenthub.monologue_agent.utils.prompts import (
    format_background_commands,
)
from opendevin.core.schema.observation import ObservationType
from opendevin.events.observation.commands import CmdOutputObservation


def test_format_background_commands():
    background_commands_obs = [
        CmdOutputObservation(
            command_id='1',
            command='python server.py',
            observation=ObservationType.RUN,
            exit_code=0,
            content='some content',
        ),
        CmdOutputObservation(
            command_id='2',
            command='npm start',
            observation=ObservationType.RUN,
            exit_code=0,
            content='some content',
        ),
    ]

    formatted_commands = format_background_commands(background_commands_obs)

    assert 'python server.py' in formatted_commands
    assert 'npm start' in formatted_commands
    assert 'The following commands are running in the background:' in formatted_commands
