from openhands.events.observation import CmdOutputMetadata, CmdOutputObservation
from openhands.events.serialization import event_to_dict


def test_command_output_success_serialization():
    # Test successful command
    obs = CmdOutputObservation(
        command='ls',
        content='file1.txt\nfile2.txt',
        metadata=CmdOutputMetadata(exit_code=0),
    )
    serialized = event_to_dict(obs)
    assert serialized['success'] is True

    # Test failed command
    obs = CmdOutputObservation(
        command='ls',
        content='No such file or directory',
        metadata=CmdOutputMetadata(exit_code=1),
    )
    serialized = event_to_dict(obs)
    assert serialized['success'] is False
