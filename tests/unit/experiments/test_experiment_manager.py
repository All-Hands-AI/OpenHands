"""Tests for experiment manager functionality, particularly condenser config override behavior."""

from unittest.mock import Mock, patch

import pytest

from openhands.core.config.agent_config import AgentConfig
from openhands.core.config.condenser_config import (
    CondenserPipelineConfig,
    LLMSummarizingCondenserConfig,
    NoOpCondenserConfig,
)
from openhands.core.config.openhands_config import OpenHandsConfig
from openhands.experiments.experiment_manager import ExperimentConfig, ExperimentManagerImpl


@patch('openhands.experiments.experiment_manager.load_experiment_config')
def test_experiment_manager_ignores_nonexistent_attributes(
    mock_load_experiment_config,
):
    """Test that experiment manager ignores attempts to set nonexistent attributes.

    The experiment manager only sets attributes that already exist on the agent config.
    Attempts to set nonexistent attributes are silently ignored.
    """
    # Create experiment config that attempts to set a nonexistent attribute
    mock_experiment_config = ExperimentConfig(
        config={'condenser_type': 'noop'}  # This attribute doesn't exist on AgentConfig
    )
    mock_load_experiment_config.return_value = mock_experiment_config

    # Create an OpenHandsConfig with a default agent config
    config = OpenHandsConfig()
    agent_config = config.get_agent_config(config.default_agent)
    agent_config.condenser = CondenserPipelineConfig()

    # Apply experiment manager changes
    modified_config = ExperimentManagerImpl.run_config_variant_test(
        'test-user', 'test-conversation', config
    )

    # Get the modified agent config
    modified_agent_config = modified_config.get_agent_config(modified_config.default_agent)

    # Verify that the condenser config was NOT changed (since condenser_type doesn't exist)
    # Should still use the original condenser config
    assert isinstance(modified_agent_config.condenser, CondenserPipelineConfig)

    # Verify that the non-existent attribute was not set
    assert not hasattr(modified_agent_config, 'condenser_type')


@patch('openhands.experiments.experiment_manager.load_experiment_config')
def test_experiment_manager_can_override_simple_attributes(
    mock_load_experiment_config,
):
    """Test that experiment manager can override simple string/boolean attributes.

    The experiment manager should be able to override simple attributes like
    enable_browsing, enable_jupyter, etc.
    """
    # Create experiment config that overrides simple attributes
    mock_experiment_config = ExperimentConfig(
        config={
            'enable_browsing': False,
            'enable_jupyter': False,
            'enable_cmd': True,
        }
    )
    mock_load_experiment_config.return_value = mock_experiment_config

    # Create an OpenHandsConfig with a default agent config
    config = OpenHandsConfig()
    agent_config = config.get_agent_config(config.default_agent)
    agent_config.enable_browsing = True
    agent_config.enable_jupyter = True
    agent_config.enable_cmd = False

    # Apply experiment manager changes
    modified_config = ExperimentManagerImpl.run_config_variant_test(
        'test-user', 'test-conversation', config
    )

    # Get the modified agent config
    modified_agent_config = modified_config.get_agent_config(modified_config.default_agent)

    # Verify that the simple attributes were overridden
    assert modified_agent_config.enable_browsing == False
    assert modified_agent_config.enable_jupyter == False
    assert modified_agent_config.enable_cmd == True


@patch('openhands.experiments.experiment_manager.load_experiment_config')
def test_experiment_manager_no_override_when_no_config(
    mock_load_experiment_config,
):
    """Test that no overrides occur when no experiment config is loaded."""
    # Mock no experiment config loaded
    mock_load_experiment_config.return_value = None

    # Create an OpenHandsConfig with a default agent config
    config = OpenHandsConfig()
    agent_config = config.get_agent_config(config.default_agent)
    agent_config.enable_browsing = True
    agent_config.condenser = CondenserPipelineConfig()

    # Apply experiment manager changes
    modified_config = ExperimentManagerImpl.run_config_variant_test(
        'test-user', 'test-conversation', config
    )

    # Get the modified agent config
    modified_agent_config = modified_config.get_agent_config(modified_config.default_agent)

    # Verify that no changes were made
    assert modified_agent_config.enable_browsing == True  # Should remain unchanged
    assert isinstance(modified_agent_config.condenser, CondenserPipelineConfig)


@patch('openhands.experiments.experiment_manager.load_experiment_config')
def test_experiment_manager_overrides_any_existing_attribute(
    mock_load_experiment_config,
):
    """Test that experiment manager overrides any existing attribute, including complex objects.

    The experiment manager doesn't distinguish between simple and complex attributes.
    It will override any attribute that exists on the agent config, even complex objects
    like condenser configs, by setting them to the value from the experiment config.
    """
    # Create experiment config that tries to override simple attributes and complex objects
    mock_experiment_config = ExperimentConfig(
        config={
            'enable_browsing': False,
            'condenser': NoOpCondenserConfig(),  # This WILL override the complex object
        }
    )
    mock_load_experiment_config.return_value = mock_experiment_config

    # Create an OpenHandsConfig with a complex condenser config
    config = OpenHandsConfig()
    agent_config = config.get_agent_config(config.default_agent)

    # Create a mock LLM config for the condenser
    from openhands.core.config.llm_config import LLMConfig
    llm_config = LLMConfig(model='gpt-4')

    original_condenser = LLMSummarizingCondenserConfig(
        llm_config=llm_config,
        keep_first=5,
        max_size=150
    )
    agent_config.condenser = original_condenser

    # Apply experiment manager changes
    modified_config = ExperimentManagerImpl.run_config_variant_test(
        'test-user', 'test-conversation', config
    )

    # Get the modified agent config
    modified_agent_config = modified_config.get_agent_config(modified_config.default_agent)

    # Verify that the complex condenser config was OVERRIDDEN with the string value
    # This shows that the experiment manager doesn't preserve complex objects
    assert modified_agent_config.condenser == NoOpCondenserConfig()
    assert not isinstance(modified_agent_config.condenser, LLMSummarizingCondenserConfig)

    # Verify that simple attributes were also overridden
    assert modified_agent_config.enable_browsing == False


@patch('openhands.experiments.experiment_manager.load_experiment_config')
def test_experiment_manager_handles_nonexistent_attributes(
    mock_load_experiment_config,
):
    """Test that experiment manager handles attempts to set nonexistent attributes gracefully."""
    # Create experiment config that tries to set nonexistent attributes
    mock_experiment_config = ExperimentConfig(
        config={
            'nonexistent_attribute': 'value',
            'another_fake_attr': 'another_value',
        }
    )
    mock_load_experiment_config.return_value = mock_experiment_config

    # Create an OpenHandsConfig
    config = OpenHandsConfig()
    agent_config = config.get_agent_config(config.default_agent)

    # Apply experiment manager changes (should not raise an exception)
    modified_config = ExperimentManagerImpl.run_config_variant_test(
        'test-user', 'test-conversation', config
    )

    # Get the modified agent config
    modified_agent_config = modified_config.get_agent_config(modified_config.default_agent)

    # Verify that nonexistent attributes were not set
    assert not hasattr(modified_agent_config, 'nonexistent_attribute')
    assert not hasattr(modified_agent_config, 'another_fake_attr')
