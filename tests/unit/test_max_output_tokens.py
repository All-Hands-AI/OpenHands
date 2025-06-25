from unittest.mock import patch

import pytest

from openhands.core.config import LLMConfig
from openhands.llm.llm import LLM


@pytest.fixture
def default_config():
    return LLMConfig(
        model='claude-sonnet-4-20250514',
        api_key='test_key',
        max_output_tokens=4096,  # Set a specific value for testing
    )


@patch('openhands.llm.llm.litellm_completion')
def test_max_output_tokens_in_config(mock_litellm_completion, default_config):
    """Test that max_output_tokens is correctly set in the config."""
    # Mock the completion response
    mock_litellm_completion.return_value = {
        'choices': [{'message': {'content': 'Test response'}}]
    }

    # Create LLM instance
    llm = LLM(default_config)

    # Verify max_output_tokens is set correctly in the config
    assert llm.config.max_output_tokens == 4096

    # Call completion to trigger the litellm call
    llm.completion(messages=[{'role': 'user', 'content': 'Hello!'}])

    # Verify max_completion_tokens was passed to litellm_completion
    mock_litellm_completion.assert_called_once()
    call_kwargs = mock_litellm_completion.call_args[1]
    assert 'max_completion_tokens' in call_kwargs
    assert call_kwargs['max_completion_tokens'] == 4096


@patch('openhands.llm.llm.litellm_completion')
def test_max_output_tokens_passed_to_anthropic(mock_litellm_completion, default_config):
    """
    Test that max_output_tokens is correctly passed to Anthropic models.

    This test verifies that when using an Anthropic model, the max_output_tokens
    value from the config is correctly passed as max_completion_tokens to litellm,
    which will then map it to max_tokens for Anthropic's API.
    """
    # Mock the completion response
    mock_litellm_completion.return_value = {
        'choices': [{'message': {'content': 'Test response'}}]
    }

    # Create LLM instance with Anthropic model
    llm = LLM(default_config)

    # Call completion to trigger the litellm call
    llm.completion(messages=[{'role': 'user', 'content': 'Hello!'}])

    # Verify max_completion_tokens was passed to litellm_completion
    mock_litellm_completion.assert_called_once()
    call_kwargs = mock_litellm_completion.call_args[1]

    # Check that max_completion_tokens is set correctly
    assert 'max_completion_tokens' in call_kwargs
    assert call_kwargs['max_completion_tokens'] == 4096

    # For Anthropic models, litellm will map max_completion_tokens to max_tokens
    # in the Anthropic API call, as we saw in the litellm code


@patch('openhands.llm.llm.litellm_completion')
def test_max_output_tokens_override_in_completion_call(
    mock_litellm_completion, default_config
):
    """Test that max_output_tokens can be overridden in the completion call."""
    # Mock the completion response
    mock_litellm_completion.return_value = {
        'choices': [{'message': {'content': 'Test response'}}]
    }

    # Create LLM instance
    llm = LLM(default_config)

    # Call completion with a different max_completion_tokens value
    llm.completion(
        messages=[{'role': 'user', 'content': 'Hello!'}],
        max_completion_tokens=2048,  # Override the config value
    )

    # Verify the overridden value was passed to litellm_completion
    mock_litellm_completion.assert_called_once()
    call_kwargs = mock_litellm_completion.call_args[1]
    assert 'max_completion_tokens' in call_kwargs
    assert call_kwargs['max_completion_tokens'] == 2048


@patch('openhands.llm.llm.litellm_completion')
def test_azure_model_uses_max_tokens_param(mock_litellm_completion):
    """Test that Azure models use max_tokens instead of max_completion_tokens."""
    # Create config for Azure model
    azure_config = LLMConfig(
        model='azure/gpt-4',
        api_key='test_key',
        max_output_tokens=3000,
    )

    # Mock the completion response
    mock_litellm_completion.return_value = {
        'choices': [{'message': {'content': 'Test response'}}]
    }

    # Create LLM instance with Azure model
    llm = LLM(azure_config)

    # Call completion to trigger the litellm call
    llm.completion(messages=[{'role': 'user', 'content': 'Hello!'}])

    # Verify max_tokens was passed to litellm_completion for Azure models
    mock_litellm_completion.assert_called_once()
    call_kwargs = mock_litellm_completion.call_args[1]

    # Check that max_tokens is set correctly for Azure models
    assert 'max_tokens' in call_kwargs
    assert call_kwargs['max_tokens'] == 3000
    assert 'max_completion_tokens' not in call_kwargs
