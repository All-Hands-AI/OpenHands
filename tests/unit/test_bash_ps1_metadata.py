import json

import pytest

from openhands.events.observation.commands import (
    CMD_OUTPUT_METADATA_PS1_REGEX,
    CMD_OUTPUT_PS1_BEGIN,
    CMD_OUTPUT_PS1_END,
    CmdOutputMetadata,
    CmdOutputObservation,
)


def test_ps1_metadata_format():
    """Test that PS1 prompt has correct format markers and proper escaping"""
    prompt = CmdOutputMetadata.to_ps1_prompt()
    print(prompt)
    assert prompt.startswith('\n###PS1JSON###\n')
    assert prompt.endswith('\n###PS1END###\n')

    # The JSON string should have quotes escaped by json.dumps, but not double-escaped
    assert '"exit_code"' in prompt, 'PS1 prompt should contain quotes escaped by json.dumps'
    assert r'\"exit_code\"' not in prompt, 'PS1 prompt should not contain double-escaped quotes'

    # Extract the JSON part
    json_str = prompt.replace('\n###PS1JSON###\n', '').replace('\n###PS1END###\n', '')

    # Should be able to parse it directly
    try:
        metadata = json.loads(json_str)
    except json.JSONDecodeError as e:
        pytest.fail(f'Failed to parse PS1 metadata JSON: {e}')


def test_ps1_metadata_shell_processing():
    r"""Test that PS1 metadata can be parsed after being processed by the shell.

    When the PS1 prompt is processed by the shell:
    1. Escaped quotes (\") become regular quotes (")
    2. Other escaped characters (\u, \h) remain as is

    This test verifies that we can parse the metadata after this shell processing.
    """
    # Get the PS1 prompt
    prompt = CmdOutputMetadata.to_ps1_prompt()

    # Extract the JSON part
    json_str = prompt.replace('\n###PS1JSON###\n', '').replace('\n###PS1END###\n', '')

    # The JSON string should be valid as is, since json.dumps already escapes quotes
    # and we're using raw strings for backslash sequences
    try:
        metadata = json.loads(json_str)
    except json.JSONDecodeError as e:
        pytest.fail(f'Failed to parse PS1 metadata JSON: {e}')

    # Check that backslash values are preserved
    assert metadata['username'] == r'\u'
    assert metadata['hostname'] == r'\h'