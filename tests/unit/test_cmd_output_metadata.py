from openhands.events.observation.commands import CmdOutputMetadata


def test_ps1_metadata_parsing():
    # Get the PS1 prompt string
    ps1_prompt = CmdOutputMetadata.to_ps1_prompt()

    # Try to parse it
    matches = CmdOutputMetadata.matches_ps1_metadata(ps1_prompt)

    # Should find exactly one match
    assert len(matches) == 1

    # Should be able to create metadata from the match
    metadata = CmdOutputMetadata.from_ps1_match(matches[0])

    # Check that fields are set to default values
    assert metadata.exit_code == -1
    assert metadata.pid == -1
    assert metadata.username == r'\u'
    assert metadata.hostname == r'\h'
    assert metadata.working_dir == '$(pwd)'
    assert metadata.py_interpreter_path == '$(which python 2>/dev/null || echo "")'
