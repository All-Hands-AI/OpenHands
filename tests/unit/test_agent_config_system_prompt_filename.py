"""Test AgentConfig system_prompt_filename functionality."""

from openhands.core.config.agent_config import AgentConfig


def test_agent_config_system_prompt_filename_default():
    """Test that AgentConfig defaults to 'system_prompt.j2' for system_prompt_filename."""
    config = AgentConfig()
    assert config.system_prompt_filename == 'system_prompt.j2'


def test_agent_config_system_prompt_filename_custom():
    """Test that AgentConfig accepts custom system_prompt_filename."""
    custom_filename = 'custom_prompt.j2'
    config = AgentConfig(system_prompt_filename=custom_filename)
    assert config.system_prompt_filename == custom_filename


def test_agent_config_system_prompt_filename_serialization():
    """Test that AgentConfig serializes and deserializes system_prompt_filename correctly."""
    custom_filename = 'custom_prompt.j2'
    config = AgentConfig(system_prompt_filename=custom_filename)

    # Test serialization
    config_dict = config.model_dump()
    assert config_dict['system_prompt_filename'] == custom_filename

    # Test deserialization
    new_config = AgentConfig.model_validate(config_dict)
    assert new_config.system_prompt_filename == custom_filename


def test_agent_config_from_toml_section_with_system_prompt_filename():
    """Test that AgentConfig.from_toml_section handles system_prompt_filename correctly."""
    data = {
        'enable_browsing': True,
        'system_prompt_filename': 'custom_prompt.j2',
        'CustomAgent': {
            'system_prompt_filename': 'custom_agent_prompt.j2',
            'enable_browsing': False,
        },
    }

    agent_mapping = AgentConfig.from_toml_section(data)

    # Check base config
    base_config = agent_mapping['agent']
    assert base_config.system_prompt_filename == 'custom_prompt.j2'
    assert base_config.enable_browsing is True

    # Check custom agent config
    custom_config = agent_mapping['CustomAgent']
    assert custom_config.system_prompt_filename == 'custom_agent_prompt.j2'
    assert custom_config.enable_browsing is False
