import copy
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from litellm import PromptTokensDetails
from litellm.exceptions import (
    RateLimitError,
)

from openhands.core.config import LLMConfig
from openhands.core.exceptions import LLMNoResponseError, OperationCancelled
from openhands.core.message import Message, TextContent
from openhands.llm.llm import LLM
from openhands.llm.metrics import Metrics, TokenUsage


@pytest.fixture(autouse=True)
def mock_logger(monkeypatch):
    # suppress logging of completion data to file
    mock_logger = MagicMock()
    monkeypatch.setattr('openhands.llm.debug_mixin.llm_prompt_logger', mock_logger)
    monkeypatch.setattr('openhands.llm.debug_mixin.llm_response_logger', mock_logger)
    monkeypatch.setattr('openhands.llm.llm.logger', mock_logger)
    return mock_logger


@pytest.fixture
def default_config():
    return LLMConfig(
        model='gpt-4o',
        api_key='test_key',
        num_retries=2,
        retry_min_wait=1,
        retry_max_wait=2,
    )


def test_llm_init_with_default_config(default_config):
    llm = LLM(default_config)
    assert llm.config.model == 'gpt-4o'
    assert llm.config.api_key.get_secret_value() == 'test_key'
    assert isinstance(llm.metrics, Metrics)
    assert llm.metrics.model_name == 'gpt-4o'


def test_token_usage_add():
    """Test that TokenUsage instances can be added together."""
    # Create two TokenUsage instances
    usage1 = TokenUsage(
        model='model1',
        prompt_tokens=10,
        completion_tokens=5,
        cache_read_tokens=3,
        cache_write_tokens=2,
        response_id='response-1',
    )

    usage2 = TokenUsage(
        model='model2',
        prompt_tokens=8,
        completion_tokens=6,
        cache_read_tokens=2,
        cache_write_tokens=4,
        response_id='response-2',
    )

    # Add them together
    combined = usage1 + usage2

    # Verify the result
    assert combined.model == 'model1'  # Should keep the model from the first instance
    assert combined.prompt_tokens == 18  # 10 + 8
    assert combined.completion_tokens == 11  # 5 + 6
    assert combined.cache_read_tokens == 5  # 3 + 2
    assert combined.cache_write_tokens == 6  # 2 + 4
    assert (
        combined.response_id == 'response-1'
    )  # Should keep the response_id from the first instance


def test_metrics_merge_accumulated_token_usage():
    """Test that accumulated token usage is properly merged between two Metrics instances."""
    # Create two Metrics instances
    metrics1 = Metrics(model_name='model1')
    metrics2 = Metrics(model_name='model2')

    # Add token usage to each
    metrics1.add_token_usage(10, 5, 3, 2, 'response-1')
    metrics2.add_token_usage(8, 6, 2, 4, 'response-2')

    # Verify initial accumulated token usage
    metrics1_data = metrics1.get()
    accumulated1 = metrics1_data['accumulated_token_usage']
    assert accumulated1['prompt_tokens'] == 10
    assert accumulated1['completion_tokens'] == 5
    assert accumulated1['cache_read_tokens'] == 3
    assert accumulated1['cache_write_tokens'] == 2

    metrics2_data = metrics2.get()
    accumulated2 = metrics2_data['accumulated_token_usage']
    assert accumulated2['prompt_tokens'] == 8
    assert accumulated2['completion_tokens'] == 6
    assert accumulated2['cache_read_tokens'] == 2
    assert accumulated2['cache_write_tokens'] == 4

    # Merge metrics2 into metrics1
    metrics1.merge(metrics2)

    # Verify merged accumulated token usage
    merged_data = metrics1.get()
    merged_accumulated = merged_data['accumulated_token_usage']
    assert merged_accumulated['prompt_tokens'] == 18  # 10 + 8
    assert merged_accumulated['completion_tokens'] == 11  # 5 + 6
    assert merged_accumulated['cache_read_tokens'] == 5  # 3 + 2
    assert merged_accumulated['cache_write_tokens'] == 6  # 2 + 4

    # Verify individual token usage records are maintained
    token_usages = merged_data['token_usages']
    assert len(token_usages) == 2
    assert token_usages[0]['response_id'] == 'response-1'
    assert token_usages[1]['response_id'] == 'response-2'


@patch('openhands.llm.llm.litellm.get_model_info')
def test_llm_init_with_model_info(mock_get_model_info, default_config):
    mock_get_model_info.return_value = {
        'max_input_tokens': 8000,
        'max_output_tokens': 2000,
    }
    llm = LLM(default_config)
    llm.init_model_info()
    assert llm.config.max_input_tokens == 8000
    assert llm.config.max_output_tokens == 2000


@patch('openhands.llm.llm.litellm.get_model_info')
def test_llm_init_without_model_info(mock_get_model_info, default_config):
    mock_get_model_info.side_effect = Exception('Model info not available')
    llm = LLM(default_config)
    llm.init_model_info()
    assert llm.config.max_input_tokens == 4096
    assert llm.config.max_output_tokens == 4096


def test_llm_init_with_custom_config():
    custom_config = LLMConfig(
        model='custom-model',
        api_key='custom_key',
        max_input_tokens=5000,
        max_output_tokens=1500,
        temperature=0.8,
        top_p=0.9,
    )
    llm = LLM(custom_config)
    assert llm.config.model == 'custom-model'
    assert llm.config.api_key.get_secret_value() == 'custom_key'
    assert llm.config.max_input_tokens == 5000
    assert llm.config.max_output_tokens == 1500
    assert llm.config.temperature == 0.8
    assert llm.config.top_p == 0.9


def test_llm_init_with_metrics():
    config = LLMConfig(model='gpt-4o', api_key='test_key')
    metrics = Metrics()
    llm = LLM(config, metrics=metrics)
    assert llm.metrics is metrics
    assert (
        llm.metrics.model_name == 'default'
    )  # because we didn't specify model_name in Metrics init


@patch('openhands.llm.llm.litellm_completion')
@patch('time.time')
def test_response_latency_tracking(mock_time, mock_litellm_completion):
    # Mock time.time() to return controlled values
    mock_time.side_effect = [1000.0, 1002.5]  # Start time, end time (2.5s difference)

    # Mock the completion response with a specific ID
    mock_response = {
        'id': 'test-response-123',
        'choices': [{'message': {'content': 'Test response'}}],
    }
    mock_litellm_completion.return_value = mock_response

    # Create LLM instance and make a completion call
    config = LLMConfig(model='gpt-4o', api_key='test_key')
    llm = LLM(config)
    response = llm.completion(messages=[{'role': 'user', 'content': 'Hello!'}])

    # Verify the response latency was tracked correctly
    assert len(llm.metrics.response_latencies) == 1
    latency_record = llm.metrics.response_latencies[0]
    assert latency_record.model == 'gpt-4o'
    assert (
        latency_record.latency == 2.5
    )  # Should be the difference between our mocked times
    assert latency_record.response_id == 'test-response-123'

    # Verify the completion response was returned correctly
    assert response['id'] == 'test-response-123'
    assert response['choices'][0]['message']['content'] == 'Test response'

    # To make sure the metrics fail gracefully, set the start/end time to go backwards.
    mock_time.side_effect = [1000.0, 999.0]
    llm.completion(messages=[{'role': 'user', 'content': 'Hello!'}])

    # There should now be 2 latencies, the last of which has the value clipped to 0
    assert len(llm.metrics.response_latencies) == 2
    latency_record = llm.metrics.response_latencies[-1]
    assert latency_record.latency == 0.0  # Should be lifted to 0 instead of being -1!


def test_llm_reset():
    llm = LLM(LLMConfig(model='gpt-4o-mini', api_key='test_key'))
    initial_metrics = copy.deepcopy(llm.metrics)
    initial_metrics.add_cost(1.0)
    initial_metrics.add_response_latency(0.5, 'test-id')
    initial_metrics.add_token_usage(10, 5, 3, 2, 'test-id')
    llm.reset()
    assert llm.metrics.accumulated_cost != initial_metrics.accumulated_cost
    assert llm.metrics.costs != initial_metrics.costs
    assert llm.metrics.response_latencies != initial_metrics.response_latencies
    assert llm.metrics.token_usages != initial_metrics.token_usages
    assert isinstance(llm.metrics, Metrics)

    # Check that accumulated token usage is reset
    metrics_data = llm.metrics.get()
    accumulated_usage = metrics_data['accumulated_token_usage']
    assert accumulated_usage['prompt_tokens'] == 0
    assert accumulated_usage['completion_tokens'] == 0
    assert accumulated_usage['cache_read_tokens'] == 0
    assert accumulated_usage['cache_write_tokens'] == 0


@patch('openhands.llm.llm.litellm.get_model_info')
def test_llm_init_with_openrouter_model(mock_get_model_info, default_config):
    default_config.model = 'openrouter:gpt-4o-mini'
    mock_get_model_info.return_value = {
        'max_input_tokens': 7000,
        'max_output_tokens': 1500,
    }
    llm = LLM(default_config)
    llm.init_model_info()
    assert llm.config.max_input_tokens == 7000
    assert llm.config.max_output_tokens == 1500
    mock_get_model_info.assert_called_once_with('openrouter:gpt-4o-mini')


# Tests involving completion and retries


@patch('openhands.llm.llm.litellm_completion')
def test_completion_with_mocked_logger(
    mock_litellm_completion, default_config, mock_logger
):
    mock_litellm_completion.return_value = {
        'choices': [{'message': {'content': 'Test response'}}]
    }

    llm = LLM(config=default_config)
    response = llm.completion(
        messages=[{'role': 'user', 'content': 'Hello!'}],
        stream=False,
    )

    assert response['choices'][0]['message']['content'] == 'Test response'
    assert mock_litellm_completion.call_count == 1

    mock_logger.debug.assert_called()


@pytest.mark.parametrize(
    'exception_class,extra_args,expected_retries',
    [
        (RateLimitError, {'llm_provider': 'test_provider', 'model': 'test_model'}, 2),
    ],
)
@patch('openhands.llm.llm.litellm_completion')
def test_completion_retries(
    mock_litellm_completion,
    default_config,
    exception_class,
    extra_args,
    expected_retries,
):
    mock_litellm_completion.side_effect = [
        exception_class('Test error message', **extra_args),
        {'choices': [{'message': {'content': 'Retry successful'}}]},
    ]

    llm = LLM(config=default_config)
    response = llm.completion(
        messages=[{'role': 'user', 'content': 'Hello!'}],
        stream=False,
    )

    assert response['choices'][0]['message']['content'] == 'Retry successful'
    assert mock_litellm_completion.call_count == expected_retries


@patch('openhands.llm.llm.litellm_completion')
def test_completion_rate_limit_wait_time(mock_litellm_completion, default_config):
    with patch('time.sleep') as mock_sleep:
        mock_litellm_completion.side_effect = [
            RateLimitError(
                'Rate limit exceeded', llm_provider='test_provider', model='test_model'
            ),
            {'choices': [{'message': {'content': 'Retry successful'}}]},
        ]

        llm = LLM(config=default_config)
        response = llm.completion(
            messages=[{'role': 'user', 'content': 'Hello!'}],
            stream=False,
        )

        assert response['choices'][0]['message']['content'] == 'Retry successful'
        assert mock_litellm_completion.call_count == 2

        mock_sleep.assert_called_once()
        wait_time = mock_sleep.call_args[0][0]
        assert (
            default_config.retry_min_wait <= wait_time <= default_config.retry_max_wait
        ), f'Expected wait time between {default_config.retry_min_wait} and {default_config.retry_max_wait} seconds, but got {wait_time}'


@patch('openhands.llm.llm.litellm_completion')
def test_completion_operation_cancelled(mock_litellm_completion, default_config):
    mock_litellm_completion.side_effect = OperationCancelled('Operation cancelled')

    llm = LLM(config=default_config)
    with pytest.raises(OperationCancelled):
        llm.completion(
            messages=[{'role': 'user', 'content': 'Hello!'}],
            stream=False,
        )

    assert mock_litellm_completion.call_count == 1


@patch('openhands.llm.llm.litellm_completion')
def test_completion_keyboard_interrupt(mock_litellm_completion, default_config):
    def side_effect(*args, **kwargs):
        raise KeyboardInterrupt('Simulated KeyboardInterrupt')

    mock_litellm_completion.side_effect = side_effect

    llm = LLM(config=default_config)
    with pytest.raises(OperationCancelled):
        try:
            llm.completion(
                messages=[{'role': 'user', 'content': 'Hello!'}],
                stream=False,
            )
        except KeyboardInterrupt:
            raise OperationCancelled('Operation cancelled due to KeyboardInterrupt')

    assert mock_litellm_completion.call_count == 1


@patch('openhands.llm.llm.litellm_completion')
def test_completion_keyboard_interrupt_handler(mock_litellm_completion, default_config):
    global _should_exit

    def side_effect(*args, **kwargs):
        global _should_exit
        _should_exit = True
        return {'choices': [{'message': {'content': 'Simulated interrupt response'}}]}

    mock_litellm_completion.side_effect = side_effect

    llm = LLM(config=default_config)
    result = llm.completion(
        messages=[{'role': 'user', 'content': 'Hello!'}],
        stream=False,
    )

    assert mock_litellm_completion.call_count == 1
    assert result['choices'][0]['message']['content'] == 'Simulated interrupt response'
    assert _should_exit

    _should_exit = False


@patch('openhands.llm.llm.litellm_completion')
def test_completion_retry_with_llm_no_response_error_zero_temp(
    mock_litellm_completion, default_config
):
    """
    Test that the retry decorator properly handles LLMNoResponseError by:
    1. First call to llm_completion uses temperature=0 and throws LLMNoResponseError
    2. Second call should have temperature=0.2 and return a successful response
    """

    # Define a side effect function that checks the temperature parameter
    # and returns different responses based on it
    def side_effect(*args, **kwargs):
        temperature = kwargs.get('temperature', 0)

        # First call with temperature=0 should raise LLMNoResponseError
        if temperature == 0:
            raise LLMNoResponseError('LLM did not return a response')

        else:
            return {
                'choices': [
                    {'message': {'content': f'Response with temperature={temperature}'}}
                ]
            }

    mock_litellm_completion.side_effect = side_effect

    # Create LLM instance and make a completion call
    llm = LLM(config=default_config)
    response = llm.completion(
        messages=[{'role': 'user', 'content': 'Hello!'}],
        stream=False,
        temperature=0,  # Initial temperature is 0
    )

    # Verify the response after retry
    assert (
        response['choices'][0]['message']['content'] == 'Response with temperature=1.0'
    )

    # Verify that litellm_completion was called twice
    assert mock_litellm_completion.call_count == 2

    # Check the temperature in the first call (should be 0)
    first_call_kwargs = mock_litellm_completion.call_args_list[0][1]
    assert first_call_kwargs.get('temperature') == 0

    # Check the temperature in the second call (should be 1.0)
    second_call_kwargs = mock_litellm_completion.call_args_list[1][1]
    assert second_call_kwargs.get('temperature') == 1.0


@patch('openhands.llm.llm.litellm_completion')
def test_completion_retry_with_llm_no_response_error_nonzero_temp(
    mock_litellm_completion, default_config
):
    """
    Test that the retry decorator works for LLMNoResponseError when initial temperature is non-zero,
    and keeps the original temperature on retry.

    This test verifies that when LLMNoResponseError is raised with a non-zero temperature:
    1. The retry mechanism is triggered
    2. The temperature remains unchanged (not set to 0.2)
    3. After all retries are exhausted, the exception is propagated
    """
    # Define a side effect function that always raises LLMNoResponseError
    mock_litellm_completion.side_effect = LLMNoResponseError(
        'LLM did not return a response'
    )

    # Create LLM instance and make a completion call with non-zero temperature
    llm = LLM(config=default_config)

    # We expect this to raise an exception after all retries are exhausted
    with pytest.raises(LLMNoResponseError):
        llm.completion(
            messages=[{'role': 'user', 'content': 'Hello!'}],
            stream=False,
            temperature=0.7,  # Initial temperature is non-zero
        )

    # Verify that litellm_completion was called multiple times (retries happened)
    # The default_config has num_retries=2, so it should be called 2 times
    assert mock_litellm_completion.call_count == 2

    # Check the temperature in the first call (should be 0.7)
    first_call_kwargs = mock_litellm_completion.call_args_list[0][1]
    assert first_call_kwargs.get('temperature') == 0.7

    # Check the temperature in the second call (should remain 0.7, not changed to 0.2)
    second_call_kwargs = mock_litellm_completion.call_args_list[1][1]
    assert second_call_kwargs.get('temperature') == 0.7


@patch('openhands.llm.llm.litellm_completion')
def test_completion_retry_with_llm_no_response_error_nonzero_temp_successful_retry(
    mock_litellm_completion, default_config
):
    """
    Test that the retry decorator works for LLMNoResponseError with non-zero temperature
    and successfully retries while preserving the original temperature.

    This test verifies that:
    1. First call to llm_completion with temperature=0.7 throws LLMNoResponseError
    2. Second call with the same temperature=0.7 returns a successful response
    """

    # Define a side effect function that raises LLMNoResponseError on first call
    # and returns a successful response on second call
    def side_effect(*args, **kwargs):
        temperature = kwargs.get('temperature', 0)

        if mock_litellm_completion.call_count == 1:
            # First call should raise LLMNoResponseError
            raise LLMNoResponseError('LLM did not return a response')
        else:
            # Second call should return a successful response
            return {
                'choices': [
                    {
                        'message': {
                            'content': f'Successful response with temperature={temperature}'
                        }
                    }
                ]
            }

    mock_litellm_completion.side_effect = side_effect

    # Create LLM instance and make a completion call with non-zero temperature
    llm = LLM(config=default_config)
    response = llm.completion(
        messages=[{'role': 'user', 'content': 'Hello!'}],
        stream=False,
        temperature=0.7,  # Non-zero temperature
    )

    # Verify the response after retry
    assert (
        response['choices'][0]['message']['content']
        == 'Successful response with temperature=0.7'
    )

    # Verify that litellm_completion was called twice
    assert mock_litellm_completion.call_count == 2

    # Check the temperature in the first call (should be 0.7)
    first_call_kwargs = mock_litellm_completion.call_args_list[0][1]
    assert first_call_kwargs.get('temperature') == 0.7

    # Check the temperature in the second call (should still be 0.7)
    second_call_kwargs = mock_litellm_completion.call_args_list[1][1]
    assert second_call_kwargs.get('temperature') == 0.7


@patch('openhands.llm.llm.litellm_completion')
def test_completion_retry_with_llm_no_response_error_successful_retry(
    mock_litellm_completion, default_config
):
    """
    Test that the retry decorator works for LLMNoResponseError with zero temperature
    and successfully retries with temperature=0.2.

    This test verifies that:
    1. First call to llm_completion with temperature=0 throws LLMNoResponseError
    2. Second call with temperature=0.2 returns a successful response
    """

    # Define a side effect function that raises LLMNoResponseError on first call
    # and returns a successful response on second call
    def side_effect(*args, **kwargs):
        temperature = kwargs.get('temperature', 0)

        if mock_litellm_completion.call_count == 1:
            # First call should raise LLMNoResponseError
            raise LLMNoResponseError('LLM did not return a response')
        else:
            # Second call should return a successful response
            return {
                'choices': [
                    {
                        'message': {
                            'content': f'Successful response with temperature={temperature}'
                        }
                    }
                ]
            }

    mock_litellm_completion.side_effect = side_effect

    # Create LLM instance and make a completion call with explicit temperature=0
    llm = LLM(config=default_config)
    response = llm.completion(
        messages=[{'role': 'user', 'content': 'Hello!'}],
        stream=False,
        temperature=0,  # Explicitly set temperature to 0
    )

    # Verify the response after retry
    assert (
        response['choices'][0]['message']['content']
        == 'Successful response with temperature=1.0'
    )

    # Verify that litellm_completion was called twice
    assert mock_litellm_completion.call_count == 2

    # Check the temperature in the first call (should be 0)
    first_call_kwargs = mock_litellm_completion.call_args_list[0][1]
    assert first_call_kwargs.get('temperature') == 0

    # Check the temperature in the second call (should be 1.0)
    second_call_kwargs = mock_litellm_completion.call_args_list[1][1]
    assert second_call_kwargs.get('temperature') == 1.0


@patch('openhands.llm.llm.litellm_completion')
def test_completion_with_litellm_mock(mock_litellm_completion, default_config):
    mock_response = {
        'choices': [{'message': {'content': 'This is a mocked response.'}}]
    }
    mock_litellm_completion.return_value = mock_response

    test_llm = LLM(config=default_config)
    response = test_llm.completion(
        messages=[{'role': 'user', 'content': 'Hello!'}],
        stream=False,
        drop_params=True,
    )

    # Assertions
    assert response['choices'][0]['message']['content'] == 'This is a mocked response.'
    mock_litellm_completion.assert_called_once()

    # Check if the correct arguments were passed to litellm_completion
    call_args = mock_litellm_completion.call_args[1]  # Get keyword arguments
    assert call_args['model'] == default_config.model
    assert call_args['messages'] == [{'role': 'user', 'content': 'Hello!'}]
    assert not call_args['stream']


@patch('openhands.llm.llm.litellm_completion')
def test_completion_with_two_positional_args(mock_litellm_completion, default_config):
    mock_response = {
        'choices': [{'message': {'content': 'Response to positional args.'}}]
    }
    mock_litellm_completion.return_value = mock_response

    test_llm = LLM(config=default_config)
    response = test_llm.completion(
        'some-model-to-be-ignored',
        [{'role': 'user', 'content': 'Hello from positional args!'}],
        stream=False,
    )

    # Assertions
    assert (
        response['choices'][0]['message']['content'] == 'Response to positional args.'
    )
    mock_litellm_completion.assert_called_once()

    # Check if the correct arguments were passed to litellm_completion
    call_args, call_kwargs = mock_litellm_completion.call_args
    assert (
        call_kwargs['model'] == default_config.model
    )  # Should use the model from config, not the first arg
    assert call_kwargs['messages'] == [
        {'role': 'user', 'content': 'Hello from positional args!'}
    ]
    assert not call_kwargs['stream']

    # Ensure the first positional argument (model) was ignored
    assert (
        len(call_args) == 0
    )  # No positional args should be passed to litellm_completion here


@patch('openhands.llm.llm.litellm.token_counter')
def test_get_token_count_with_dict_messages(mock_token_counter, default_config):
    mock_token_counter.return_value = 42
    llm = LLM(default_config)
    messages = [{'role': 'user', 'content': 'Hello!'}]

    token_count = llm.get_token_count(messages)

    assert token_count == 42
    mock_token_counter.assert_called_once_with(
        model=default_config.model, messages=messages, custom_tokenizer=None
    )


@patch('openhands.llm.llm.litellm.token_counter')
def test_get_token_count_with_message_objects(
    mock_token_counter, default_config, mock_logger
):
    llm = LLM(default_config)

    # Create a Message object and its equivalent dict
    message_obj = Message(role='user', content=[TextContent(text='Hello!')])
    message_dict = {'role': 'user', 'content': 'Hello!'}

    # Mock token counter to return different values for each call
    mock_token_counter.side_effect = [42, 42]  # Same value for both cases

    # Get token counts for both formats
    token_count_obj = llm.get_token_count([message_obj])
    token_count_dict = llm.get_token_count([message_dict])

    # Verify both formats get the same token count
    assert token_count_obj == token_count_dict
    assert mock_token_counter.call_count == 2


@patch('openhands.llm.llm.litellm.token_counter')
@patch('openhands.llm.llm.create_pretrained_tokenizer')
def test_get_token_count_with_custom_tokenizer(
    mock_create_tokenizer, mock_token_counter, default_config
):
    mock_tokenizer = MagicMock()
    mock_create_tokenizer.return_value = mock_tokenizer
    mock_token_counter.return_value = 42

    config = copy.deepcopy(default_config)
    config.custom_tokenizer = 'custom/tokenizer'
    llm = LLM(config)
    messages = [{'role': 'user', 'content': 'Hello!'}]

    token_count = llm.get_token_count(messages)

    assert token_count == 42
    mock_create_tokenizer.assert_called_once_with('custom/tokenizer')
    mock_token_counter.assert_called_once_with(
        model=config.model, messages=messages, custom_tokenizer=mock_tokenizer
    )


@patch('openhands.llm.llm.litellm.token_counter')
def test_get_token_count_error_handling(
    mock_token_counter, default_config, mock_logger
):
    mock_token_counter.side_effect = Exception('Token counting failed')
    llm = LLM(default_config)
    messages = [{'role': 'user', 'content': 'Hello!'}]

    token_count = llm.get_token_count(messages)

    assert token_count == 0
    mock_token_counter.assert_called_once()
    mock_logger.error.assert_called_once_with(
        'Error getting token count for\n model gpt-4o\nToken counting failed'
    )


@patch('openhands.llm.llm.litellm_completion')
def test_llm_token_usage(mock_litellm_completion, default_config):
    # This mock response includes usage details with prompt_tokens,
    # completion_tokens, prompt_tokens_details.cached_tokens, and model_extra.cache_creation_input_tokens
    mock_response_1 = {
        'id': 'test-response-usage',
        'choices': [{'message': {'content': 'Usage test response'}}],
        'usage': {
            'prompt_tokens': 12,
            'completion_tokens': 3,
            'prompt_tokens_details': PromptTokensDetails(cached_tokens=2),
            'model_extra': {'cache_creation_input_tokens': 5},
        },
    }

    # Create a second usage scenario to test accumulation and a different response_id
    mock_response_2 = {
        'id': 'test-response-usage-2',
        'choices': [{'message': {'content': 'Second usage test response'}}],
        'usage': {
            'prompt_tokens': 7,
            'completion_tokens': 2,
            'prompt_tokens_details': PromptTokensDetails(cached_tokens=1),
            'model_extra': {'cache_creation_input_tokens': 3},
        },
    }

    # We'll make mock_litellm_completion return these responses in sequence
    mock_litellm_completion.side_effect = [mock_response_1, mock_response_2]

    llm = LLM(config=default_config)

    # First call
    llm.completion(messages=[{'role': 'user', 'content': 'Hello usage!'}])

    # Verify we have exactly one usage record after first call
    token_usage_list = llm.metrics.get()['token_usages']
    assert len(token_usage_list) == 1
    usage_entry_1 = token_usage_list[0]
    assert usage_entry_1['prompt_tokens'] == 12
    assert usage_entry_1['completion_tokens'] == 3
    assert usage_entry_1['cache_read_tokens'] == 2
    assert usage_entry_1['cache_write_tokens'] == 5
    assert usage_entry_1['response_id'] == 'test-response-usage'

    # Second call
    llm.completion(messages=[{'role': 'user', 'content': 'Hello again!'}])

    # Now we expect two usage records total
    token_usage_list = llm.metrics.get()['token_usages']
    assert len(token_usage_list) == 2
    usage_entry_2 = token_usage_list[-1]
    assert usage_entry_2['prompt_tokens'] == 7
    assert usage_entry_2['completion_tokens'] == 2
    assert usage_entry_2['cache_read_tokens'] == 1
    assert usage_entry_2['cache_write_tokens'] == 3
    assert usage_entry_2['response_id'] == 'test-response-usage-2'


@patch('openhands.llm.llm.litellm_completion')
def test_accumulated_token_usage(mock_litellm_completion, default_config):
    """Test that token usage is properly accumulated across multiple LLM calls."""
    # Mock responses with token usage information
    mock_response_1 = {
        'id': 'test-response-1',
        'choices': [{'message': {'content': 'First response'}}],
        'usage': {
            'prompt_tokens': 10,
            'completion_tokens': 5,
            'prompt_tokens_details': PromptTokensDetails(cached_tokens=3),
            'model_extra': {'cache_creation_input_tokens': 4},
        },
    }

    mock_response_2 = {
        'id': 'test-response-2',
        'choices': [{'message': {'content': 'Second response'}}],
        'usage': {
            'prompt_tokens': 8,
            'completion_tokens': 6,
            'prompt_tokens_details': PromptTokensDetails(cached_tokens=2),
            'model_extra': {'cache_creation_input_tokens': 3},
        },
    }

    # Set up the mock to return these responses in sequence
    mock_litellm_completion.side_effect = [mock_response_1, mock_response_2]

    # Create LLM instance
    llm = LLM(config=default_config)

    # First call
    llm.completion(messages=[{'role': 'user', 'content': 'First message'}])

    # Check accumulated token usage after first call
    metrics_data = llm.metrics.get()
    accumulated_usage = metrics_data['accumulated_token_usage']

    assert accumulated_usage['prompt_tokens'] == 10
    assert accumulated_usage['completion_tokens'] == 5
    assert accumulated_usage['cache_read_tokens'] == 3
    assert accumulated_usage['cache_write_tokens'] == 4

    # Second call
    llm.completion(messages=[{'role': 'user', 'content': 'Second message'}])

    # Check accumulated token usage after second call
    metrics_data = llm.metrics.get()
    accumulated_usage = metrics_data['accumulated_token_usage']

    # Values should be the sum of both calls
    assert accumulated_usage['prompt_tokens'] == 18  # 10 + 8
    assert accumulated_usage['completion_tokens'] == 11  # 5 + 6
    assert accumulated_usage['cache_read_tokens'] == 5  # 3 + 2
    assert accumulated_usage['cache_write_tokens'] == 7  # 4 + 3

    # Verify individual token usage records are still maintained
    token_usages = metrics_data['token_usages']
    assert len(token_usages) == 2

    # First record
    assert token_usages[0]['prompt_tokens'] == 10
    assert token_usages[0]['completion_tokens'] == 5
    assert token_usages[0]['cache_read_tokens'] == 3
    assert token_usages[0]['cache_write_tokens'] == 4
    assert token_usages[0]['response_id'] == 'test-response-1'

    # Second record
    assert token_usages[1]['prompt_tokens'] == 8
    assert token_usages[1]['completion_tokens'] == 6
    assert token_usages[1]['cache_read_tokens'] == 2
    assert token_usages[1]['cache_write_tokens'] == 3
    assert token_usages[1]['response_id'] == 'test-response-2'


@patch('openhands.llm.llm.litellm_completion')
def test_completion_with_log_completions(mock_litellm_completion, default_config):
    with tempfile.TemporaryDirectory() as temp_dir:
        default_config.log_completions = True
        default_config.log_completions_folder = temp_dir
        mock_response = {
            'choices': [{'message': {'content': 'This is a mocked response.'}}]
        }
        mock_litellm_completion.return_value = mock_response

        test_llm = LLM(config=default_config)
        response = test_llm.completion(
            messages=[{'role': 'user', 'content': 'Hello!'}],
            stream=False,
            drop_params=True,
        )
        assert (
            response['choices'][0]['message']['content'] == 'This is a mocked response.'
        )
        files = list(Path(temp_dir).iterdir())
        # Expect a log to be generated
        assert len(files) == 1
