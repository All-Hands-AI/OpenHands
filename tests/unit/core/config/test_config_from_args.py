"""Tests for the ConfigurationMerger.from_args method."""
import argparse
import os
from unittest.mock import patch, MagicMock

import pytest

from openhands.core.config import OpenHandsConfig
from openhands.core.config.configuration_merger import ConfigurationMerger
from openhands.core.config.llm_config import LLMConfig


@pytest.fixture
def mock_args():
    """Create a mock args object for testing."""
    args = argparse.Namespace()
    args.config_file = 'config.toml'
    args.llm_config = None
    args.agent_cls = None
    args.max_iterations = None
    args.max_budget_per_task = None
    args.selected_repo = None
    return args


@patch('openhands.core.config.utils.load_openhands_config')
def test_from_args_basic(mock_load_config, mock_args):
    """Test that from_args returns the config from load_openhands_config when no args are set."""
    # Setup
    mock_config = OpenHandsConfig()
    mock_load_config.return_value = mock_config
    
    # Execute
    result = ConfigurationMerger.from_args(mock_args)
    
    # Verify
    mock_load_config.assert_called_once_with(config_file='config.toml')
    assert result is mock_config


@patch('openhands.core.config.utils.load_openhands_config')
def test_from_args_with_llm_config(mock_load_config, mock_args):
    """Test that from_args sets the LLM config when specified in args."""
    # Setup
    mock_config = OpenHandsConfig()
    mock_config.llms = {'test_llm': LLMConfig(model='test-model')}
    mock_load_config.return_value = mock_config
    mock_args.llm_config = 'test_llm'
    
    # Execute
    result = ConfigurationMerger.from_args(mock_args)
    
    # Verify
    assert result.get_llm_config().model == 'test-model'


@patch('openhands.core.config.utils.load_openhands_config')
@patch('openhands.core.config.utils.get_llm_config_arg')
def test_from_args_with_llm_config_not_in_config(mock_get_llm_config, mock_load_config, mock_args):
    """Test that from_args loads the LLM config from file when not in loaded configs."""
    # Setup
    mock_config = OpenHandsConfig()
    mock_config.llms = {}
    mock_load_config.return_value = mock_config
    mock_args.llm_config = 'test_llm'
    
    test_llm_config = LLMConfig(model='test-model')
    mock_get_llm_config.return_value = test_llm_config
    
    # Execute
    result = ConfigurationMerger.from_args(mock_args)
    
    # Verify
    mock_get_llm_config.assert_called_once_with('test_llm', 'config.toml')
    assert result.get_llm_config() is test_llm_config


@patch('openhands.core.config.utils.load_openhands_config')
def test_from_args_with_agent_cls(mock_load_config, mock_args):
    """Test that from_args sets the agent class when specified in args."""
    # Setup
    mock_config = OpenHandsConfig()
    mock_load_config.return_value = mock_config
    mock_args.agent_cls = 'test_agent'
    
    # Execute
    result = ConfigurationMerger.from_args(mock_args)
    
    # Verify
    assert result.default_agent == 'test_agent'


@patch('openhands.core.config.utils.load_openhands_config')
def test_from_args_with_max_iterations(mock_load_config, mock_args):
    """Test that from_args sets max_iterations when specified in args."""
    # Setup
    mock_config = OpenHandsConfig()
    mock_load_config.return_value = mock_config
    mock_args.max_iterations = 10
    
    # Execute
    result = ConfigurationMerger.from_args(mock_args)
    
    # Verify
    assert result.max_iterations == 10


@patch('openhands.core.config.utils.load_openhands_config')
def test_from_args_with_max_budget_per_task(mock_load_config, mock_args):
    """Test that from_args sets max_budget_per_task when specified in args."""
    # Setup
    mock_config = OpenHandsConfig()
    mock_load_config.return_value = mock_config
    mock_args.max_budget_per_task = 100
    
    # Execute
    result = ConfigurationMerger.from_args(mock_args)
    
    # Verify
    assert result.max_budget_per_task == 100


@patch('openhands.core.config.utils.load_openhands_config')
def test_from_args_with_selected_repo(mock_load_config, mock_args):
    """Test that from_args sets selected_repo when specified in args."""
    # Setup
    mock_config = OpenHandsConfig()
    mock_load_config.return_value = mock_config
    mock_args.selected_repo = 'test_repo'
    
    # Execute
    result = ConfigurationMerger.from_args(mock_args)
    
    # Verify
    assert result.sandbox.selected_repo == 'test_repo'