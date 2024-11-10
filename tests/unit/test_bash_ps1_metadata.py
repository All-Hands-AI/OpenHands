import json

from openhands.events.observation.commands import CmdOutputMetadata


def test_ps1_metadata_format():
    """Test that PS1 prompt has correct format markers"""
    prompt = CmdOutputMetadata.to_ps1_prompt()
    assert prompt.startswith('###PS1JSON###\n')
    assert prompt.endswith('###PS1END###\n')
    print(prompt)


def test_ps1_metadata_json_structure():
    """Test that PS1 prompt contains valid JSON with expected fields"""
    prompt = CmdOutputMetadata.to_ps1_prompt()
    # Extract JSON content between markers
    json_str = prompt.replace('###PS1JSON###\n', '').replace('\n###PS1END###\n', '')
    data = json.loads(json_str)

    # Check required fields
    expected_fields = {
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
