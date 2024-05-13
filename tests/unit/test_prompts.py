import json

from agenthub.monologue_agent.utils.prompts import (
    format_background_commands,
    generate_action_prompt_with_defaults,
)
from opendevin.core.schema.observation import ObservationType
from opendevin.events.observation.commands import CmdOutputObservation


def test_generate_action_prompt_with_defaults():
    task_description = 'Fix the bug in the code.'
    user = 'test_user'
    timeout = '60'
    prompt = generate_action_prompt_with_defaults(
        task=task_description, user=user, timeout=timeout
    )

    assert task_description in prompt
    assert user in prompt
    assert timeout in prompt
    assert 'What is your next single thought or action?' in prompt


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


def test_generate_action_prompt_with_events():
    # Prepare mock events
    default_events = [
        {'event': 'default_event_1', 'details': 'Some default event details'}
    ]
    recent_events = [
        {'event': 'recent_event_1', 'details': 'Some recent event details'}
    ]

    # Call the function with complex kwargs
    prompt = generate_action_prompt_with_defaults(
        task='Complete the implementation',
        default_events=default_events,
        recent_events=recent_events,
    )

    # Verify the output contains information from the mock events
    assert 'default_event_1' in prompt
    assert 'Some default event details' in prompt
    assert 'recent_event_1' in prompt
    assert 'Some recent event details' in prompt
    assert 'Complete the implementation' in prompt


def test_generate_action_prompt_with_all_parameters():
    input_kwargs = {
        'task': 'Task1',
        'default_events': [{'action': 'start', 'args': {'key': 'value'}}],
        'recent_events': [{'action': 'update', 'args': {'key': 'value2'}}],
        'background_commands': [
            CmdOutputObservation(
                command_id=1,
                command='ls',
                observation=ObservationType.RUN,
                exit_code=0,
                content='some content',
            )
        ],
        'hint': 'Next step',
        'user': 'opendevin',
        'timeout': '30',
    }
    expected_parts = [
        '"action": "start",\n    "args": {\n      "key": "value"\n    }\n  },\n  {\n    "action": "update",\n    "args": {\n      "key": "value2"\n    }',
        'The following commands are running in the background:\n`1`: ls\nYou can end any process by sending a `kill` action with the numerical `id` above.',
        'Next step',
        'opendevin',
        '30',
    ]
    check_prompt(input_kwargs, expected_parts)


def test_generate_action_prompt_with_empty_lists():
    input_kwargs = {
        'task': 'Task2',
        'default_events': [],
        'recent_events': [],
        'background_commands': [],
        'user': 'opendevin',
    }
    expected_part = 'Task2'
    check_prompt(input_kwargs, expected_part)


def test_generate_action_prompt_with_missing_parameters():
    input_kwargs = {
        'task': 'Task3',
        'default_events': [{'action': 'end', 'args': {'key': 'value3'}}],
    }
    expected_part = 'Task3'
    check_prompt(input_kwargs, expected_part)


def test_generate_action_prompt_with_json_formatting():
    input_kwargs = {
        'task': 'Task4',
        'default_events': [{'action': 'log', 'args': {'detail': 'test'}}],
        'recent_events': [{'action': 'log', 'args': {'detail': 'test2'}}],
    }
    expected_part = '"action": "log"'
    check_prompt(input_kwargs, expected_part)


def check_prompt(input_kwargs, expected_parts):
    # Generate the prompt
    result = generate_action_prompt_with_defaults(**input_kwargs)

    # Check if expected parts are in the resulting string
    if isinstance(expected_parts, str):
        expected_parts = [expected_parts]
    for expected_part in expected_parts:
        assert expected_part in result

    # Check JSON string of events in monologue key
    monologue = []
    if 'default_events' in input_kwargs and input_kwargs['default_events'] is not None:
        monologue.extend(input_kwargs['default_events'])
    if 'recent_events' in input_kwargs and input_kwargs['recent_events'] is not None:
        monologue.extend(input_kwargs['recent_events'])
    if monologue:
        assert json.dumps(monologue, indent=2) in result

    # Check inclusion of background commands
    if 'background_commands' in input_kwargs and input_kwargs['background_commands']:
        formatted = format_background_commands(input_kwargs['background_commands'])
        assert formatted in result

