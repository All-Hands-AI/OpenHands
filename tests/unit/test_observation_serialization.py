from openhands.events.observation import (
    CmdOutputObservation,
    Observation,
)
from openhands.events.serialization import (
    event_from_dict,
    event_to_dict,
    event_to_memory,
    event_to_trajectory,
)


def serialization_deserialization(
    original_observation_dict, cls, max_message_chars: int = 10000
):
    observation_instance = event_from_dict(original_observation_dict)
    assert isinstance(
        observation_instance, Observation
    ), 'The observation instance should be an instance of Action.'
    assert isinstance(
        observation_instance, cls
    ), 'The observation instance should be an instance of CmdOutputObservation.'
    serialized_observation_dict = event_to_dict(observation_instance)
    serialized_observation_trajectory = event_to_trajectory(observation_instance)
    serialized_observation_memory = event_to_memory(
        observation_instance, max_message_chars
    )
    assert (
        serialized_observation_dict == original_observation_dict
    ), 'The serialized observation should match the original observation dict.'
    assert (
        serialized_observation_trajectory == original_observation_dict
    ), 'The serialized observation trajectory should match the original observation dict.'
    original_observation_dict.pop('message', None)
    original_observation_dict.pop('id', None)
    original_observation_dict.pop('timestamp', None)
    assert (
        serialized_observation_memory == original_observation_dict
    ), 'The serialized observation memory should match the original observation dict.'


# Additional tests for various observation subclasses can be included here
def test_observation_event_props_serialization_deserialization():
    original_observation_dict = {
        'id': 42,
        'source': 'agent',
        'timestamp': '2021-08-01T12:00:00',
        'observation': 'run',
        'message': 'Command `ls -l` executed with exit code 0.',
        'extras': {
            'exit_code': 0,
            'command': 'ls -l',
            'command_id': 3,
            'hidden': False,
            'interpreter_details': '',
        },
        'content': 'foo.txt',
    }
    serialization_deserialization(original_observation_dict, CmdOutputObservation)


def test_command_output_observation_serialization_deserialization():
    original_observation_dict = {
        'observation': 'run',
        'extras': {
            'exit_code': 0,
            'command': 'ls -l',
            'command_id': 3,
            'hidden': False,
            'interpreter_details': '',
        },
        'message': 'Command `ls -l` executed with exit code 0.',
        'content': 'foo.txt',
    }
    serialization_deserialization(original_observation_dict, CmdOutputObservation)
