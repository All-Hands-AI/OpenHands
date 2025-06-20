"""Test AgentConfig system_prompt_path functionality."""

from openhands.core.config.agent_config import AgentConfig


def test_agent_config_system_prompt_path_default():
    """Test that AgentConfig defaults to None for system_prompt_path."""
    config = AgentConfig()
    assert config.system_prompt_path is None


def test_agent_config_system_prompt_path_custom():
    """Test that AgentConfig accepts custom system_prompt_path."""
    custom_path = '/path/to/custom/prompt.j2'
    config = AgentConfig(system_prompt_path=custom_path)
    assert config.system_prompt_path == custom_path


def test_agent_config_system_prompt_path_serialization():
    """Test that AgentConfig serializes and deserializes system_prompt_path correctly."""
    custom_path = '/path/to/custom/prompt.j2'
    config = AgentConfig(system_prompt_path=custom_path)

    # Test serialization
    config_dict = config.model_dump()
    assert config_dict['system_prompt_path'] == custom_path

    # Test deserialization
    new_config = AgentConfig.model_validate(config_dict)
    assert new_config.system_prompt_path == custom_path


def test_agent_config_from_toml_section_with_system_prompt_path():
    """Test that AgentConfig.from_toml_section handles system_prompt_path correctly."""
    data = {
        'enable_browsing': True,
        'system_prompt_path': '/custom/prompt.j2',
        'CustomAgent': {
            'system_prompt_path': '/custom/agent/prompt.j2',
            'enable_browsing': False,
        },
    }

    agent_mapping = AgentConfig.from_toml_section(data)

    # Check base config
    base_config = agent_mapping['agent']
    assert base_config.system_prompt_path == '/custom/prompt.j2'
    assert base_config.enable_browsing is True

    # Check custom agent config
    custom_config = agent_mapping['CustomAgent']
    assert custom_config.system_prompt_path == '/custom/agent/prompt.j2'
    assert custom_config.enable_browsing is False
