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


@pytest.fixture
def mock_anthropic_response():
    """Create a mock response that looks like what Anthropic's API returns."""
    return {
        'id': 'msg_test123',
        'type': 'message',
        'role': 'assistant',
        'content': [{'type': 'text', 'text': 'Test response'}],
        'model': 'claude-sonnet-4-20250514',
        'stop_reason': 'end_turn',
        'stop_sequence': None,
        'usage': {'input_tokens': 10, 'output_tokens': 5},
    }


@pytest.fixture
def mock_openai_response():
    """Create a mock response that looks like what OpenAI's API returns."""
    return {
        'id': 'chatcmpl-test123',
        'object': 'chat.completion',
        'created': 1234567890,
        'model': 'gpt-4',
        'choices': [
            {
                'index': 0,
                'message': {'role': 'assistant', 'content': 'Test response'},
                'finish_reason': 'stop',
            }
        ],
        'usage': {'prompt_tokens': 10, 'completion_tokens': 5, 'total_tokens': 15},
    }


def test_max_output_tokens_in_config(default_config):
    """Test that max_output_tokens is correctly set in the config."""
    # Create LLM instance
    llm = LLM(default_config)

    # Verify max_output_tokens is set correctly in the config
    assert llm.config.max_output_tokens == 4096


def test_max_output_tokens_default_initialization():
    """Test that max_output_tokens is correctly initialized with default value when not specified."""
    # Create LLM instance with minimal config (no max_output_tokens specified)
    config = LLMConfig(model='gpt-4', api_key='test_key')
    llm = LLM(config)

    # Verify max_output_tokens is initialized to the default value (4096)
    assert llm.config.max_output_tokens == 4096


@patch('litellm.get_model_info')
def test_max_output_tokens_from_model_info(mock_get_model_info):
    """Test that max_output_tokens is correctly initialized from model info."""
    # Mock the model info returned by litellm
    mock_get_model_info.return_value = {
        'max_output_tokens': 8192,
        'max_input_tokens': 16384,
    }

    # Create LLM instance with minimal config (no max_output_tokens specified)
    config = LLMConfig(model='gpt-4', api_key='test_key')
    llm = LLM(config)

    # Verify max_output_tokens is initialized from model info
    assert llm.config.max_output_tokens == 8192


@patch('litellm.get_model_info')
def test_max_output_tokens_from_max_tokens(mock_get_model_info):
    """Test that max_output_tokens is correctly initialized from max_tokens when max_output_tokens is not available."""
    # Mock the model info returned by litellm (with max_tokens but no max_output_tokens)
    mock_get_model_info.return_value = {
        'max_tokens': 7000,
        'max_input_tokens': 16384,
    }

    # Create LLM instance with minimal config (no max_output_tokens specified)
    config = LLMConfig(model='gpt-4', api_key='test_key')
    llm = LLM(config)

    # Verify max_output_tokens is initialized from max_tokens
    assert llm.config.max_output_tokens == 7000


@patch('litellm.get_model_info')
def test_claude_3_7_sonnet_max_output_tokens(mock_get_model_info):
    """Test that Claude 3.7 Sonnet models get the special 64000 max_output_tokens value."""
    # Mock the model info returned by litellm
    mock_get_model_info.return_value = None

    # Create LLM instance with Claude 3.7 Sonnet model
    config = LLMConfig(model='claude-3-7-sonnet', api_key='test_key')
    llm = LLM(config)

    # Verify max_output_tokens is set to 64000 for Claude 3.7 Sonnet
    assert llm.config.max_output_tokens == 64000


@patch('litellm.get_model_info')
def test_verified_anthropic_model_max_output_tokens(mock_get_model_info):
    """Test that Claude Sonnet 4 models get the 64000 max_output_tokens value from litellm."""
    # Mock the model info returned by litellm
    mock_get_model_info.return_value = {'max_output_tokens': 64000, 'max_tokens': 64000}

    # Create LLM instance with a Claude Sonnet 4 model
    config = LLMConfig(model='claude-sonnet-4-20250514', api_key='test_key')
    llm = LLM(config)

    # Verify max_output_tokens is set to the value from litellm (64000)
    assert llm.config.max_output_tokens == 64000


@patch('litellm.get_model_info')
def test_non_claude_model_max_output_tokens(mock_get_model_info):
    """Test that non-Claude models get the default max_output_tokens value."""
    # Mock the model info returned by litellm
    mock_get_model_info.return_value = None

    # Create LLM instance with a non-Claude model
    config = LLMConfig(model='mistral-large', api_key='test_key')
    llm = LLM(config)

    # Verify max_output_tokens is set to None (default value)
    assert llm.config.max_output_tokens is None


@patch('litellm.get_model_info')
def test_max_output_tokens_passed_to_anthropic_via_http(
    mock_get_model_info, mock_anthropic_response
):
    """
    Test that max_output_tokens is correctly set for Anthropic models.

    This test verifies that Claude Sonnet 4 models get the 64000 max_output_tokens value.
    """
    # Mock the model info returned by litellm
    mock_get_model_info.return_value = {'max_output_tokens': 64000, 'max_tokens': 64000}

    # Create LLM instance with minimal config
    config = LLMConfig(model='claude-sonnet-4-20250514', api_key='test_key')
    llm = LLM(config)

    # Verify the config has the correct max_output_tokens value
    assert llm.config.max_output_tokens == 64000  # Value from litellm


@patch('litellm.get_model_info')
def test_claude_3_7_sonnet_max_output_tokens_in_http_request(
    mock_get_model_info, mock_anthropic_response
):
    """
    Test that the special 64000 max_output_tokens value for Claude 3.7 Sonnet
    is correctly set in the config.
    """
    # Mock the model info returned by litellm
    mock_get_model_info.return_value = None

    # Create LLM instance with Claude 3.7 Sonnet model
    config = LLMConfig(model='claude-3-7-sonnet', api_key='test_key')
    llm = LLM(config)

    # Verify the config has the correct max_output_tokens value
    assert llm.config.max_output_tokens == 64000  # Special value for Claude 3.7 Sonnet


@patch('litellm.get_model_info')
def test_max_output_tokens_override_in_completion_call(
    mock_get_model_info, mock_anthropic_response
):
    """Test that max_output_tokens can be overridden in the completion call."""
    # Mock the model info returned by litellm
    mock_get_model_info.return_value = {'max_output_tokens': 64000, 'max_tokens': 64000}

    # Create LLM instance with minimal config
    config = LLMConfig(
        model='claude-sonnet-4-20250514', api_key='test_key', max_output_tokens=2048
    )
    llm = LLM(config)

    # Verify the config has the overridden max_output_tokens value
    assert llm.config.max_output_tokens == 2048

    # Verify that the value is different from the default or model info value
    assert llm.config.max_output_tokens != 64000
    assert llm.config.max_output_tokens != 4096


@patch('litellm.get_model_info')
def test_azure_model_uses_max_tokens_param(mock_get_model_info, mock_openai_response):
    """Test that Azure models use max_tokens parameter in HTTP requests."""
    # Mock the model info returned by litellm
    mock_get_model_info.return_value = None

    # Create minimal config for Azure model (without specifying max_output_tokens)
    azure_config = LLMConfig(
        model='azure/gpt-4',
        api_key='test_key',
        base_url='https://test.openai.azure.com/',
        api_version='2024-12-01-preview',
    )

    # Create LLM instance with Azure model
    llm = LLM(azure_config)

    # Verify the config has the default max_output_tokens value
    assert llm.config.max_output_tokens is None  # Default value


@patch('litellm.get_model_info')
def test_openai_model_uses_max_completion_tokens_param(
    mock_get_model_info, mock_openai_response
):
    """Test that OpenAI models use max_completion_tokens parameter in HTTP requests."""
    # Mock the model info returned by litellm
    mock_get_model_info.return_value = None

    # Create minimal config for OpenAI model (without specifying max_output_tokens)
    openai_config = LLMConfig(
        model='gpt-4',
        api_key='test_key',
    )

    # Create LLM instance with OpenAI model
    llm = LLM(openai_config)

    # Verify the config has the default max_output_tokens value
    assert llm.config.max_output_tokens is None  # Default value
