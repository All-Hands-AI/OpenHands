# EDIT: Fixing the failing test by adding content parameter

from openhands.events.observation.files import FileEditObservation
from openhands.events.serialization.observation import observation_to_dict


def test_file_edit_observation_serialization():
    """Test that FileEditObservation is properly serialized with edit_summary and language."""
    # Create a simple file edit observation
    obs = FileEditObservation(
        path='test.py',
        prev_exist=True,
        old_content="print('hello')",
        new_content="print('world')",
        content='Edit summary of changes',  # Added the required content parameter
    )

    # Serialize the observation
    result = observation_to_dict(obs)

    # Check that the basic fields are present
    assert 'observation' in result
    assert 'content' in result
    assert 'extras' in result

    # Check that edit_summary and language are included for FileEditObservation
    assert 'edit_summary' in result['extras']
    assert 'language' in result['extras']

    # Verify the language is correctly identified from extension
    assert result['extras']['language'] == 'python'

    # Verify edit_summary has expected structure
    assert 'type' in result['extras']['edit_summary']
    assert result['extras']['edit_summary']['type'] == 'modification'
