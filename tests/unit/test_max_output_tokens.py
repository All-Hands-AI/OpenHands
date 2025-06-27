import json
from unittest.mock import MagicMock, patch

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


@patch('litellm.llms.custom_httpx.http_handler.HTTPHandler.post')
def test_max_output_tokens_passed_to_anthropic_via_http(
    mock_http_post, default_config, mock_anthropic_response
):
    """
    Test that max_output_tokens is correctly passed to Anthropic models via HTTP.

    This test mocks the actual HTTP request that litellm makes to Anthropic's API
    and verifies that the max_tokens parameter is correctly included in the request body.
    """
    # Set up the mock HTTP response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers = {'content-type': 'application/json'}
    mock_response.text = json.dumps(mock_anthropic_response)
    mock_response.json.return_value = mock_anthropic_response
    mock_http_post.return_value = mock_response

    # Create LLM instance with Anthropic model
    llm = LLM(default_config)

    # Call completion to trigger the HTTP request
    llm.completion(messages=[{'role': 'user', 'content': 'Hello!'}])

    # Verify that HTTPHandler.post was called
    mock_http_post.assert_called_once()

    # Get the call arguments
    call_args, call_kwargs = mock_http_post.call_args

    # Verify that the request was made to Anthropic's API
    assert 'anthropic.com' in call_args[0] or 'anthropic.com' in str(
        call_kwargs.get('url', '')
    )

    # Check that the request body contains max_tokens
    # The data is passed as a JSON string in the 'data' parameter
    request_data_str = call_kwargs.get('data', '{}')
    request_data = json.loads(request_data_str)
    assert 'max_tokens' in request_data
    assert request_data['max_tokens'] == 4096


@patch('litellm.llms.custom_httpx.http_handler.HTTPHandler.post')
def test_max_output_tokens_override_in_completion_call(
    mock_http_post, default_config, mock_anthropic_response
):
    """Test that max_output_tokens can be overridden in the completion call."""
    # Set up the mock HTTP response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers = {'content-type': 'application/json'}
    mock_response.text = json.dumps(mock_anthropic_response)
    mock_response.json.return_value = mock_anthropic_response
    mock_http_post.return_value = mock_response

    # Create LLM instance
    llm = LLM(default_config)

    # Call completion with a different max_completion_tokens value
    llm.completion(
        messages=[{'role': 'user', 'content': 'Hello!'}],
        max_completion_tokens=2048,  # Override the config value
    )

    # Verify that HTTPHandler.post was called
    mock_http_post.assert_called_once()

    # Get the call arguments
    call_args, call_kwargs = mock_http_post.call_args

    # Check that the request body contains the overridden max_tokens value
    request_data_str = call_kwargs.get('data', '{}')
    request_data = json.loads(request_data_str)
    assert 'max_tokens' in request_data
    assert request_data['max_tokens'] == 2048


@patch(
    'litellm.llms.azure.azure.AzureChatCompletion.make_sync_azure_openai_chat_completion_request'
)
def test_azure_model_uses_max_tokens_param(mock_azure_request, mock_openai_response):
    """Test that Azure models use max_tokens parameter in HTTP requests."""
    # Create config for Azure model
    azure_config = LLMConfig(
        model='azure/gpt-4',
        api_key='test_key',
        base_url='https://test.openai.azure.com/',
        api_version='2024-12-01-preview',
        max_output_tokens=3000,
    )

    # Mock the Azure request method to capture the data being sent
    mock_headers = {'content-type': 'application/json'}

    # Create a proper mock response that matches the expected structure
    from litellm import Message as LiteLLMMessage
    from litellm.types.utils import Choices, ModelResponse, Usage

    mock_choice = Choices(
        finish_reason='stop',
        index=0,
        message=LiteLLMMessage(content='Test response', role='assistant'),
    )

    mock_response = ModelResponse(
        id='test-id',
        choices=[mock_choice],
        created=1234567890,
        model='gpt-4',
        object='chat.completion',
        usage=Usage(prompt_tokens=10, completion_tokens=5, total_tokens=15),
    )

    mock_azure_request.return_value = (mock_headers, mock_response)

    # Create LLM instance with Azure model
    llm = LLM(azure_config)

    # Call completion to trigger the Azure request
    llm.completion(messages=[{'role': 'user', 'content': 'Hello!'}])

    # Verify that the Azure request method was called
    mock_azure_request.assert_called_once()

    # Get the call arguments to examine the data being sent
    call_args, call_kwargs = mock_azure_request.call_args

    # The data should be in the call_kwargs as 'data'
    data = call_kwargs.get('data', {})

    # Check that the request contains max_tokens (not max_completion_tokens)
    assert 'max_tokens' in data
    assert data['max_tokens'] == 3000
    # Ensure max_completion_tokens is not used for Azure models
    assert 'max_completion_tokens' not in data


@patch(
    'litellm.llms.openai.openai.OpenAIChatCompletion.make_sync_openai_chat_completion_request'
)
def test_openai_model_uses_max_completion_tokens_param(
    mock_openai_request, mock_openai_response
):
    """Test that OpenAI models use max_completion_tokens parameter in HTTP requests."""
    # Create config for OpenAI model
    openai_config = LLMConfig(
        model='gpt-4',
        api_key='test_key',
        max_output_tokens=2048,
    )

    # Mock the OpenAI request method to capture the data being sent
    # Create a proper mock response that matches the expected structure
    from litellm import Message as LiteLLMMessage
    from litellm.types.utils import Choices, ModelResponse, Usage

    mock_choice = Choices(
        finish_reason='stop',
        index=0,
        message=LiteLLMMessage(content='Test response', role='assistant'),
    )

    mock_response = ModelResponse(
        id='test-id',
        choices=[mock_choice],
        created=1234567890,
        model='gpt-4',
        object='chat.completion',
        usage=Usage(prompt_tokens=10, completion_tokens=5, total_tokens=15),
    )

    mock_headers = {'content-type': 'application/json'}
    mock_openai_request.return_value = (mock_headers, mock_response)

    # Create LLM instance with OpenAI model
    llm = LLM(openai_config)

    # Call completion to trigger the OpenAI request
    llm.completion(messages=[{'role': 'user', 'content': 'Hello!'}])

    # Verify that the OpenAI request method was called
    mock_openai_request.assert_called_once()

    # Get the call arguments to examine the data being sent
    call_args, call_kwargs = mock_openai_request.call_args

    # The data should be in the call_kwargs as 'data'
    data = call_kwargs.get('data', {})

    # Check that the request contains max_completion_tokens
    assert 'max_completion_tokens' in data
    assert data['max_completion_tokens'] == 2048
