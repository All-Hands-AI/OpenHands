import json

from openhands.events.observation.commands import (
    CMD_OUTPUT_METADATA_PS1_REGEX,
    CMD_OUTPUT_PS1_BEGIN,
    CMD_OUTPUT_PS1_END,
    CmdOutputMetadata,
    CmdOutputObservation,
)


def test_ps1_metadata_format():
    """Test that PS1 prompt has correct format markers."""
    prompt = CmdOutputMetadata.to_ps1_prompt()
    print(prompt)
    assert prompt.startswith('\n###PS1JSON###\n')
    assert prompt.endswith('\n###PS1END###\n')
    assert r'\"exit_code\"' in prompt, 'PS1 prompt should contain escaped double quotes'


def test_ps1_metadata_json_structure():
    """Test that PS1 prompt contains valid JSON with expected fields."""
    prompt = CmdOutputMetadata.to_ps1_prompt()
    # Extract JSON content between markers
    json_str = prompt.replace('###PS1JSON###\n', '').replace('\n###PS1END###\n', '')
    # Remove escaping before parsing
    json_str = json_str.replace(r'\"', '"')
    # Remove any trailing content after the JSON
    json_str = json_str.split('###PS1END###')[0].strip()
    data = json.loads(json_str)

    # Check required fields
    expected_fields = {
        'pid',
        'exit_code',
        'username',
        'hostname',
        'working_dir',
        'py_interpreter_path',
    }
    assert set(data.keys()) == expected_fields


def test_ps1_metadata_parsing():
    """Test parsing PS1 output into CmdOutputMetadata."""
    test_data = {
        'exit_code': 0,
        'username': 'testuser',
        'hostname': 'localhost',
        'working_dir': '/home/testuser',
        'py_interpreter_path': '/usr/bin/python',
    }

    ps1_str = f"""###PS1JSON###
{json.dumps(test_data, indent=2)}
###PS1END###
"""
    matches = CmdOutputMetadata.matches_ps1_metadata(ps1_str)
    assert len(matches) == 1
    metadata = CmdOutputMetadata.from_ps1_match(matches[0])
    assert metadata.exit_code == test_data['exit_code']
    assert metadata.username == test_data['username']
    assert metadata.hostname == test_data['hostname']
    assert metadata.working_dir == test_data['working_dir']
    assert metadata.py_interpreter_path == test_data['py_interpreter_path']


def test_ps1_metadata_parsing_string():
    """Test parsing PS1 output into CmdOutputMetadata."""
    ps1_str = r"""###PS1JSON###
{
  "exit_code": "0",
  "username": "myname",
  "hostname": "myhostname",
  "working_dir": "~/mydir",
  "py_interpreter_path": "/my/python/path"
}
###PS1END###
"""
    matches = CmdOutputMetadata.matches_ps1_metadata(ps1_str)
    assert len(matches) == 1
    metadata = CmdOutputMetadata.from_ps1_match(matches[0])
    assert metadata.exit_code == 0
    assert metadata.username == 'myname'
    assert metadata.hostname == 'myhostname'
    assert metadata.working_dir == '~/mydir'
    assert metadata.py_interpreter_path == '/my/python/path'


def test_ps1_metadata_parsing_string_real_example():
    """Test parsing PS1 output into CmdOutputMetadata."""
    ps1_str = r"""
###PS1JSON###
{
  "pid": "",
  "exit_code": "0",
  "username": "runner",
  "hostname": "fv-az1055-610",
  "working_dir": "/home/runner/work/OpenHands/OpenHands",
  "py_interpreter_path": "/home/runner/.cache/pypoetry/virtualenvs/openhands-ai-ULPBlkAi-py3.12/bin/python"
}
###PS1END###
"""
    matches = CmdOutputMetadata.matches_ps1_metadata(ps1_str)
    assert len(matches) == 1
    metadata = CmdOutputMetadata.from_ps1_match(matches[0])
    assert metadata.exit_code == 0
    assert metadata.username == 'runner'
    assert metadata.hostname == 'fv-az1055-610'
    assert metadata.working_dir == '/home/runner/work/OpenHands/OpenHands'
    assert (
        metadata.py_interpreter_path
        == '/home/runner/.cache/pypoetry/virtualenvs/openhands-ai-ULPBlkAi-py3.12/bin/python'
    )


def test_ps1_metadata_parsing_additional_prefix():
    """Test parsing PS1 output into CmdOutputMetadata."""
    test_data = {
        'exit_code': 0,
        'username': 'testuser',
        'hostname': 'localhost',
        'working_dir': '/home/testuser',
        'py_interpreter_path': '/usr/bin/python',
    }

    ps1_str = f"""
This is something that not part of the PS1 prompt

###PS1JSON###
{json.dumps(test_data, indent=2)}
###PS1END###
"""

    matches = CmdOutputMetadata.matches_ps1_metadata(ps1_str)
    assert len(matches) == 1
    metadata = CmdOutputMetadata.from_ps1_match(matches[0])
    assert metadata.exit_code == test_data['exit_code']
    assert metadata.username == test_data['username']
    assert metadata.hostname == test_data['hostname']
    assert metadata.working_dir == test_data['working_dir']
    assert metadata.py_interpreter_path == test_data['py_interpreter_path']


def test_ps1_metadata_parsing_invalid():
    """Test parsing invalid PS1 output returns default metadata."""
    # Test with invalid JSON
    invalid_json = """###PS1JSON###
    {invalid json}
###PS1END###
"""
    matches = CmdOutputMetadata.matches_ps1_metadata(invalid_json)
    assert len(matches) == 0  # No matches should be found for invalid JSON

    # Test with missing markers
    invalid_format = """NOT A VALID PS1 PROMPT"""
    matches = CmdOutputMetadata.matches_ps1_metadata(invalid_format)
    assert len(matches) == 0

    # Test with empty PS1 metadata
    empty_metadata = """###PS1JSON###

###PS1END###
"""
    matches = CmdOutputMetadata.matches_ps1_metadata(empty_metadata)
    assert len(matches) == 0  # No matches should be found for empty metadata

    # Test with whitespace in PS1 metadata
    whitespace_metadata = """###PS1JSON###

    {
        "exit_code": "0",
        "pid": "123",
        "username": "test",
        "hostname": "localhost",
        "working_dir": "/home/test",
        "py_interpreter_path": "/usr/bin/python"
    }

###PS1END###
"""
    matches = CmdOutputMetadata.matches_ps1_metadata(whitespace_metadata)
    assert len(matches) == 1
    metadata = CmdOutputMetadata.from_ps1_match(matches[0])
    assert metadata.exit_code == 0
    assert metadata.pid == 123


def test_ps1_metadata_missing_fields():
    """Test handling of missing fields in PS1 metadata."""
    # Test with only required fields
    minimal_data = {'exit_code': 0, 'pid': 123}
    ps1_str = f"""###PS1JSON###
{json.dumps(minimal_data)}
###PS1END###
"""
    matches = CmdOutputMetadata.matches_ps1_metadata(ps1_str)
    assert len(matches) == 1
    metadata = CmdOutputMetadata.from_ps1_match(matches[0])
    assert metadata.exit_code == 0
    assert metadata.pid == 123
    assert metadata.username is None
    assert metadata.hostname is None
    assert metadata.working_dir is None
    assert metadata.py_interpreter_path is None

    # Test with missing exit_code but valid pid
    no_exit_code = {'pid': 123, 'username': 'test'}
    ps1_str = f"""###PS1JSON###
{json.dumps(no_exit_code)}
###PS1END###
"""
    matches = CmdOutputMetadata.matches_ps1_metadata(ps1_str)
    assert len(matches) == 1
    metadata = CmdOutputMetadata.from_ps1_match(matches[0])
    assert metadata.exit_code == -1  # default value
    assert metadata.pid == 123
    assert metadata.username == 'test'


def test_ps1_metadata_multiple_blocks():
    """Test handling multiple PS1 metadata blocks."""
    test_data = {
        'exit_code': 0,
        'username': 'testuser',
        'hostname': 'localhost',
        'working_dir': '/home/testuser',
        'py_interpreter_path': '/usr/bin/python',
    }

    ps1_str = f"""###PS1JSON###
{json.dumps(test_data, indent=2)}
###PS1END###
Some other content
###PS1JSON###
{json.dumps(test_data, indent=2)}
###PS1END###
"""
    matches = CmdOutputMetadata.matches_ps1_metadata(ps1_str)
    assert len(matches) == 2  # Should find both blocks
    # Both blocks should parse successfully
    metadata1 = CmdOutputMetadata.from_ps1_match(matches[0])
    metadata2 = CmdOutputMetadata.from_ps1_match(matches[1])
    assert metadata1.exit_code == test_data['exit_code']
    assert metadata2.exit_code == test_data['exit_code']


def test_ps1_metadata_regex_pattern():
    """Test the regex pattern used to extract PS1 metadata."""
    # Test basic pattern matching
    test_str = f'{CMD_OUTPUT_PS1_BEGIN}test\n{CMD_OUTPUT_PS1_END}'
    matches = CMD_OUTPUT_METADATA_PS1_REGEX.finditer(test_str)
    match = next(matches)
    assert match.group(1).strip() == 'test'

    # Test with content before and after
    test_str = f'prefix\n{CMD_OUTPUT_PS1_BEGIN}test\n{CMD_OUTPUT_PS1_END}suffix'
    matches = CMD_OUTPUT_METADATA_PS1_REGEX.finditer(test_str)
    match = next(matches)
    assert match.group(1).strip() == 'test'

    # Test with multiline content
    test_str = f'{CMD_OUTPUT_PS1_BEGIN}line1\nline2\nline3\n{CMD_OUTPUT_PS1_END}'
    matches = CMD_OUTPUT_METADATA_PS1_REGEX.finditer(test_str)
    match = next(matches)
    assert match.group(1).strip() == 'line1\nline2\nline3'


def test_cmd_output_observation_properties():
    """Test CmdOutputObservation class properties."""
    # Test with successful command
    metadata = CmdOutputMetadata(exit_code=0, pid=123)
    obs = CmdOutputObservation(command='ls', content='file1\nfile2', metadata=metadata)
    assert obs.command_id == 123
    assert obs.exit_code == 0
    assert not obs.error
    assert 'exit code 0' in obs.message
    assert 'ls' in obs.message
    assert 'file1' in str(obs)
    assert 'file2' in str(obs)
    assert 'metadata' in str(obs)

    # Test with failed command
    metadata = CmdOutputMetadata(exit_code=1, pid=456)
    obs = CmdOutputObservation(command='invalid', content='error', metadata=metadata)
    assert obs.command_id == 456
    assert obs.exit_code == 1
    assert obs.error
    assert 'exit code 1' in obs.message
    assert 'invalid' in obs.message
    assert 'error' in str(obs)


def test_ps1_metadata_empty_fields():
    """Test handling of empty fields in PS1 metadata."""
    # Test with empty strings
    empty_data = {
        'exit_code': 0,
        'pid': 123,
        'username': '',
        'hostname': '',
        'working_dir': '',
        'py_interpreter_path': '',
    }
    ps1_str = f"""###PS1JSON###
{json.dumps(empty_data)}
###PS1END###
"""
    matches = CmdOutputMetadata.matches_ps1_metadata(ps1_str)
    assert len(matches) == 1
    metadata = CmdOutputMetadata.from_ps1_match(matches[0])
    assert metadata.exit_code == 0
    assert metadata.pid == 123
    assert metadata.username == ''
    assert metadata.hostname == ''
    assert metadata.working_dir == ''
    assert metadata.py_interpreter_path == ''

    # Test with malformed but valid JSON
    malformed_json = """###PS1JSON###
    {
        "exit_code":0,
        "pid"  :  123,
        "username":    "test"  ,
        "hostname": "host",
        "working_dir"    :"dir",
        "py_interpreter_path":"path"
    }
###PS1END###
"""
    matches = CmdOutputMetadata.matches_ps1_metadata(malformed_json)
    assert len(matches) == 1
    metadata = CmdOutputMetadata.from_ps1_match(matches[0])
    assert metadata.exit_code == 0
    assert metadata.pid == 123
    assert metadata.username == 'test'
    assert metadata.hostname == 'host'
    assert metadata.working_dir == 'dir'
    assert metadata.py_interpreter_path == 'path'
