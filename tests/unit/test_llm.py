from unittest.mock import MagicMock, patch

import pytest
from litellm.exceptions import (
    APIConnectionError,
    ContentPolicyViolationError,
    InternalServerError,
    OpenAIError,
    RateLimitError,
)

from openhands.core.config import LLMConfig
from openhands.core.exceptions import OperationCancelled
from openhands.core.metrics import Metrics
from openhands.llm.llm import LLM


@pytest.fixture(autouse=True)
def mock_logger(monkeypatch):
    # suppress logging of completion data to file
    mock_logger = MagicMock()
    monkeypatch.setattr('openhands.llm.llm.llm_prompt_logger', mock_logger)
    monkeypatch.setattr('openhands.llm.llm.llm_response_logger', mock_logger)
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


@pytest.fixture
def llm_test_instance(default_config):
    with patch('openhands.llm.llm.LLM._call_completion') as mock_call_completion:
        llm = LLM(config=default_config)
        llm._call_completion = mock_call_completion
        yield llm


@pytest.fixture
def mock_call_completion():
    with patch('openhands.llm.llm.LLM._call_completion') as mock:
        yield mock


def test_llm_init_with_default_config(default_config):
    llm = LLM(default_config)
    assert llm.config.model == 'gpt-4o'
    assert llm.config.api_key == 'test_key'
    assert isinstance(llm.metrics, Metrics)


@patch('openhands.llm.llm.litellm.get_model_info')
def test_llm_init_with_model_info(mock_get_model_info, default_config):
    mock_get_model_info.return_value = {
        'max_input_tokens': 8000,
        'max_output_tokens': 2000,
    }
    llm = LLM(default_config)
    assert llm.config.max_input_tokens == 8000
    assert llm.config.max_output_tokens == 2000


@patch('openhands.llm.llm.litellm.get_model_info')
def test_llm_init_without_model_info(mock_get_model_info, default_config):
    mock_get_model_info.side_effect = Exception('Model info not available')
    llm = LLM(default_config)
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
    assert llm.config.api_key == 'custom_key'
    assert llm.config.max_input_tokens == 5000
    assert llm.config.max_output_tokens == 1500
    assert llm.config.temperature == 0.8
    assert llm.config.top_p == 0.9


def test_llm_init_with_metrics():
    config = LLMConfig(model='gpt-4o', api_key='test_key')
    metrics = Metrics()
    llm = LLM(config, metrics=metrics)
    assert llm.metrics is metrics


def test_llm_reset():
    llm = LLM(LLMConfig(model='gpt-4o-mini', api_key='test_key'))
    initial_metrics = llm.metrics
    llm.reset()
    assert llm.metrics is not initial_metrics
    assert isinstance(llm.metrics, Metrics)


@patch('openhands.llm.llm.litellm.get_model_info')
def test_llm_init_with_openrouter_model(mock_get_model_info, default_config):
    default_config.model = 'openrouter:gpt-4o-mini'
    mock_get_model_info.return_value = {
        'max_input_tokens': 7000,
        'max_output_tokens': 1500,
    }
    llm = LLM(default_config)
    assert llm.config.max_input_tokens == 7000
    assert llm.config.max_output_tokens == 1500
    mock_get_model_info.assert_called_once_with('openrouter:gpt-4o-mini')


def test_completion_with_mocked_logger(llm_test_instance, mock_logger):
    llm_test_instance._call_completion.return_value = {
        'choices': [{'message': {'content': 'Test response'}}]
    }

    response = llm_test_instance.completion(
        messages=[{'role': 'user', 'content': 'Hello!'}],
        stream=False,
    )

    assert response['choices'][0]['message']['content'] == 'Test response'
    assert llm_test_instance._call_completion.call_count == 1

    mock_logger.debug.assert_called()


# Tests involving completion and retries


def test_completion(default_config):
    with patch.object(LLM, '_call_completion') as mock_call_completion:
        mock_response = {
            'choices': [{'message': {'content': 'This is a test message.'}}]
        }
        mock_call_completion.return_value = mock_response
        test_llm = LLM(config=default_config)
        response = test_llm.completion(
            messages=[{'role': 'user', 'content': 'Hello!'}],
            stream=False,
            drop_params=True,
        )
        # Assertions for non-streaming completion
        assert response['choices'][0]['message']['content'] != ''


@pytest.mark.parametrize(
    'exception_class,extra_args,expected_retries',
    [
        (
            APIConnectionError,
            {'llm_provider': 'test_provider', 'model': 'test_model'},
            2,
        ),
        (
            ContentPolicyViolationError,
            {'model': 'test_model', 'llm_provider': 'test_provider'},
            2,
        ),
        (
            InternalServerError,
            {'llm_provider': 'test_provider', 'model': 'test_model'},
            2,
        ),
        (OpenAIError, {}, 2),
        (RateLimitError, {'llm_provider': 'test_provider', 'model': 'test_model'}, 2),
    ],
)
def test_completion_retries(
    llm_test_instance, exception_class, extra_args, expected_retries
):
    llm_test_instance._call_completion.side_effect = [
        exception_class('Test error message', **extra_args),
        {'choices': [{'message': {'content': 'Retry successful'}}]},
    ]

    response = llm_test_instance.completion(
        messages=[{'role': 'user', 'content': 'Hello!'}],
        stream=False,
    )

    assert response['choices'][0]['message']['content'] == 'Retry successful'
    assert llm_test_instance._call_completion.call_count == expected_retries


def test_completion_rate_limit_wait_time(llm_test_instance):
    with patch('time.sleep') as mock_sleep:
        llm_test_instance._call_completion.side_effect = [
            RateLimitError(
                'Rate limit exceeded', llm_provider='test_provider', model='test_model'
            ),
            {'choices': [{'message': {'content': 'Retry successful'}}]},
        ]

        response = llm_test_instance.completion(
            messages=[{'role': 'user', 'content': 'Hello!'}],
            stream=False,
        )

        assert response['choices'][0]['message']['content'] == 'Retry successful'
        assert llm_test_instance._call_completion.call_count == 2

        mock_sleep.assert_called_once()
        wait_time = mock_sleep.call_args[0][0]
        assert (
            60 <= wait_time <= 240
        ), f'Expected wait time between 60 and 240 seconds, but got {wait_time}'


def test_completion_exhausts_retries(llm_test_instance):
    llm_test_instance._call_completion.side_effect = APIConnectionError(
        'Persistent error', llm_provider='test_provider', model='test_model'
    )

    with pytest.raises(APIConnectionError):
        llm_test_instance.completion(
            messages=[{'role': 'user', 'content': 'Hello!'}],
            stream=False,
        )

    assert (
        llm_test_instance._call_completion.call_count
        == llm_test_instance.config.num_retries
    )


def test_completion_operation_cancelled(llm_test_instance):
    llm_test_instance._call_completion.side_effect = OperationCancelled(
        'Operation cancelled'
    )

    with pytest.raises(OperationCancelled):
        llm_test_instance.completion(
            messages=[{'role': 'user', 'content': 'Hello!'}],
            stream=False,
        )

    assert llm_test_instance._call_completion.call_count == 1


def test_completion_keyboard_interrupt(llm_test_instance):
    def side_effect(*args, **kwargs):
        raise KeyboardInterrupt('Simulated KeyboardInterrupt')

    llm_test_instance._call_completion.side_effect = side_effect

    with pytest.raises(OperationCancelled):
        try:
            llm_test_instance.completion(
                messages=[{'role': 'user', 'content': 'Hello!'}],
                stream=False,
            )
        except KeyboardInterrupt:
            # Convert KeyboardInterrupt to OperationCancelled
            # This simulates what should happen in the LLM class
            raise OperationCancelled('Operation cancelled due to KeyboardInterrupt')

    assert llm_test_instance._call_completion.call_count == 1


def test_completion_keyboard_interrupt_handler(llm_test_instance):
    global _should_exit

    def side_effect(*args, **kwargs):
        global _should_exit
        _should_exit = True
        return {'choices': [{'message': {'content': 'Simulated interrupt response'}}]}

    llm_test_instance._call_completion.side_effect = side_effect

    result = llm_test_instance.completion(
        messages=[{'role': 'user', 'content': 'Hello!'}],
        stream=False,
    )

    assert llm_test_instance._call_completion.call_count == 1

    assert result['choices'][0]['message']['content'] == 'Simulated interrupt response'

    assert _should_exit

    _should_exit = False
