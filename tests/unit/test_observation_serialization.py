from opendevin.events.observation import (
    CmdOutputObservation,
    Observation,
    observation_from_dict,
)


def test_observation_serialization_deserialization():
    original_observation_dict = {
        'observation': 'run',
        'extras': {'exit_code': 0, 'command': 'ls -l', 'command_id': 3},
        'message': 'Command `ls -l` executed with exit code 0.',
        'content': 'foo.txt',
    }
    observation_instance = observation_from_dict(original_observation_dict)
    assert isinstance(
        observation_instance, Observation
    ), 'The observation instance should be an instance of Action.'
    assert isinstance(
        observation_instance, CmdOutputObservation
    ), 'The observation instance should be an instance of AgentThinkAction.'
    serialized_observation_dict = observation_instance.to_dict()
    serialized_observation_memory = observation_instance.to_memory()
    assert (
        serialized_observation_dict == original_observation_dict
    ), 'The serialized observation should match the original observation dict.'
    original_observation_dict.pop('message')
    assert (
        serialized_observation_memory == original_observation_dict
    ), 'The serialized observation in memory should match the original observation dict.'


# Additional tests for various observation subclasses can be included here
