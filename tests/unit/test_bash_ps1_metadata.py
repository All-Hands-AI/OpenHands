import json

from openhands.events.observation.commands import (
    CmdOutputMetadata,
    CmdOutputObservation,
    CMD_OUTPUT_PS1_BEGIN,
    CMD_OUTPUT_PS1_END,
    CMD_OUTPUT_METADATA_PS1_REGEX,
)


def test_ps1_metadata_format():
    """Test that PS1 prompt has correct format markers"""
    prompt = CmdOutputMetadata.to_ps1_prompt()
    assert prompt.startswith('###PS1JSON###\n')
    assert prompt.endswith('###PS1END###\n')
    assert r'\"exit_code\"' in prompt, "PS1 prompt should contain escaped double quotes"
    print(prompt)


def test_ps1_metadata_json_structure():
    """Test that PS1 prompt contains valid JSON with expected fields"""
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
    """Test parsing PS1 output into CmdOutputMetadata"""
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

    metadata = CmdOutputMetadata.from_ps1(ps1_str)
    assert metadata.exit_code == test_data['exit_code']
    assert metadata.username == test_data['username']
    assert metadata.hostname == test_data['hostname']
    assert metadata.working_dir == test_data['working_dir']
    assert metadata.py_interpreter_path == test_data['py_interpreter_path']



def test_ps1_metadata_parsing_additional_prefix():
    """Test parsing PS1 output into CmdOutputMetadata"""
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

    metadata = CmdOutputMetadata.from_ps1(ps1_str)
    assert metadata.exit_code == test_data['exit_code']
    assert metadata.username == test_data['username']
    assert metadata.hostname == test_data['hostname']
    assert metadata.working_dir == test_data['working_dir']
    assert metadata.py_interpreter_path == test_data['py_interpreter_path']


def test_ps1_metadata_parsing_invalid():
    """Test parsing invalid PS1 output returns default metadata"""
    # Test with invalid JSON
    invalid_json = """###PS1JSON###
    {invalid json}
###PS1END###
"""
    metadata = CmdOutputMetadata.from_ps1(invalid_json)
    assert isinstance(metadata, CmdOutputMetadata)
    assert metadata.exit_code == -1  # default value

    # Test with missing markers
    invalid_format = """{"exit_code": 0}"""
    metadata = CmdOutputMetadata.from_ps1(invalid_format)
    assert isinstance(metadata, CmdOutputMetadata)
    assert metadata.exit_code == -1  # default value

    # Test with empty PS1 metadata
    empty_metadata = """###PS1JSON###

###PS1END###
"""
    metadata = CmdOutputMetadata.from_ps1(empty_metadata)
    assert isinstance(metadata, CmdOutputMetadata)
    assert metadata.exit_code == -1  # default value

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
    metadata = CmdOutputMetadata.from_ps1(whitespace_metadata)
    assert isinstance(metadata, CmdOutputMetadata)
    assert metadata.exit_code == 0
    assert metadata.pid == 123


def test_ps1_metadata_missing_fields():
    """Test handling of missing fields in PS1 metadata"""
    # Test with only required fields
    minimal_data = {
        'exit_code': 0,
        'pid': 123
    }
    ps1_str = f"""###PS1JSON###
{json.dumps(minimal_data)}
###PS1END###
"""
    metadata = CmdOutputMetadata.from_ps1(ps1_str)
    assert metadata.exit_code == 0
    assert metadata.pid == 123
    assert metadata.username is None
    assert metadata.hostname is None
    assert metadata.working_dir is None
    assert metadata.py_interpreter_path is None

    # Test with missing exit_code but valid pid
    no_exit_code = {
        'pid': 123,
        'username': 'test'
    }
    ps1_str = f"""###PS1JSON###
{json.dumps(no_exit_code)}
###PS1END###
"""
    metadata = CmdOutputMetadata.from_ps1(ps1_str)
    assert metadata.exit_code == -1  # default value
    assert metadata.pid == 123
    assert metadata.username == 'test'


def test_ps1_metadata_malformed_values():
    """Test handling of malformed values in PS1 metadata"""
    # Test with non-integer exit_code and pid
    malformed_data = {
        'exit_code': 'not_an_int',
        'pid': 'abc',
        'username': 'test'
    }
    ps1_str = f"""###PS1JSON###
{json.dumps(malformed_data)}
###PS1END###
"""
    # Should return default metadata for numeric fields when parsing fails
    # but keep valid string fields
    metadata = CmdOutputMetadata.from_ps1(ps1_str)
    assert metadata.exit_code == -1
    assert metadata.pid == -1
    assert metadata.username == 'test'

    # Test with boolean values for numeric fields
    boolean_data = {
        'exit_code': True,
        'pid': False,
        'username': 'test'
    }
    ps1_str = f"""###PS1JSON###
{json.dumps(boolean_data)}
###PS1END###
"""
    metadata = CmdOutputMetadata.from_ps1(ps1_str)
    assert metadata.exit_code == 1  # True converts to 1
    assert metadata.pid == 0  # False converts to 0
    assert metadata.username == 'test'

    # Test with float values for numeric fields
    float_data = {
        'exit_code': 1.5,
        'pid': 2.7,
        'username': 'test'
    }
    ps1_str = f"""###PS1JSON###
{json.dumps(float_data)}
###PS1END###
"""
    metadata = CmdOutputMetadata.from_ps1(ps1_str)
    assert metadata.exit_code == 1  # Float should be truncated
    assert metadata.pid == 2  # Float should be truncated
    assert metadata.username == 'test'

    # Test with None values for numeric fields
    none_data = {
        'exit_code': None,
        'pid': None,
        'username': 'test'
    }
    ps1_str = f"""###PS1JSON###
{json.dumps(none_data)}
###PS1END###
"""
    metadata = CmdOutputMetadata.from_ps1(ps1_str)
    assert metadata.exit_code == -1  # Should use default value
    assert metadata.pid == -1  # Should use default value
    assert metadata.username == 'test'


def test_ps1_metadata_multiple_blocks():
    """Test that an error is raised when multiple PS1 metadata blocks are present"""
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

    import pytest
    with pytest.raises(ValueError, match="Multiple PS1 metadata blocks detected"):
        CmdOutputMetadata.from_ps1(ps1_str)


def test_ps1_metadata_regex_pattern():
    """Test the regex pattern used to extract PS1 metadata"""
    # Test basic pattern matching
    test_str = "###PS1JSON###\ntest\n###PS1END###\n"
    matches = CMD_OUTPUT_METADATA_PS1_REGEX.finditer(test_str)
    match = next(matches)
    assert match.group(1) == "test"

    # Test with different line endings
    test_str = "###PS1JSON###\r\ntest\r\n###PS1END###\r\n"
    matches = CMD_OUTPUT_METADATA_PS1_REGEX.finditer(test_str)
    match = next(matches)
    assert match.group(1) == "test"

    # Test with content before and after
    test_str = "prefix\n###PS1JSON###\ntest\n###PS1END###\nsuffix"
    matches = CMD_OUTPUT_METADATA_PS1_REGEX.finditer(test_str)
    match = next(matches)
    assert match.group(1) == "test"

    # Test with multiline content
    test_str = "###PS1JSON###\nline1\nline2\nline3\n###PS1END###\n"
    matches = CMD_OUTPUT_METADATA_PS1_REGEX.finditer(test_str)
    match = next(matches)
    assert match.group(1) == "line1\nline2\nline3"


def test_cmd_output_observation_properties():
    """Test CmdOutputObservation class properties"""
    # Test with successful command
    metadata = CmdOutputMetadata(exit_code=0, pid=123)
    obs = CmdOutputObservation(command="ls", content="file1\nfile2", metadata=metadata)
    assert obs.command_id == 123
    assert obs.exit_code == 0
    assert not obs.error
    assert "exit code 0" in obs.message
    assert "ls" in obs.message
    assert "file1" in str(obs)
    assert "file2" in str(obs)
    assert "metadata" in str(obs)

    # Test with failed command
    metadata = CmdOutputMetadata(exit_code=1, pid=456)
    obs = CmdOutputObservation(command="invalid", content="error", metadata=metadata)
    assert obs.command_id == 456
    assert obs.exit_code == 1
    assert obs.error
    assert "exit code 1" in obs.message
    assert "invalid" in obs.message
    assert "error" in str(obs)


def test_ps1_metadata_empty_fields():
    """Test handling of empty fields in PS1 metadata"""
    # Test with empty strings
    empty_data = {
        'exit_code': 0,
        'pid': 123,
        'username': '',
        'hostname': '',
        'working_dir': '',
        'py_interpreter_path': ''
    }
    ps1_str = f"""###PS1JSON###
{json.dumps(empty_data)}
###PS1END###
"""
    metadata = CmdOutputMetadata.from_ps1(ps1_str)
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
    metadata = CmdOutputMetadata.from_ps1(malformed_json)
    assert metadata.exit_code == 0
    assert metadata.pid == 123
    assert metadata.username == 'test'
    assert metadata.hostname == 'host'
    assert metadata.working_dir == 'dir'
    assert metadata.py_interpreter_path == 'path'
