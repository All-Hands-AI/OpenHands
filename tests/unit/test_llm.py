from unittest.mock import MagicMock, patch

import pytest
import toml
from litellm.exceptions import (
    APIConnectionError,
    InternalServerError,
    RateLimitError,
    ServiceUnavailableError,
)

from openhands.core.config import LLMConfig
from openhands.core.exceptions import OperationCancelled
from openhands.core.metrics import Metrics
from openhands.llm.llm import LLM


@pytest.fixture(autouse=True)
def mock_logger(monkeypatch):
    # suppress logging of completion data to file
    mock_logger = MagicMock()
    monkeypatch.setattr('openhands.llm.debug_mixin.llm_prompt_logger', mock_logger)
    monkeypatch.setattr('openhands.llm.debug_mixin.llm_response_logger', mock_logger)
    return mock_logger


@pytest.fixture
def default_config():
    return LLMConfig(
        model='openai/gpt-4o',
        api_key='test_key',
        num_retries=2,
        retry_min_wait=1,
        retry_max_wait=2,
    )


@pytest.fixture
def router_config():
    model_list = [
        {
            'model_name': 'gpt-3.5-turbo',
            'litellm_params': {
                'model': 'gpt-3.5-turbo',
                'api_key': 'OPENAI_API_KEY',
                'max_retries': 3,
            },
            'model_info': {'id': '1234'},
            'tpm': 100000,
            'rpm': 10000,
        },
        {
            'model_name': 'claude-3-5-sonnet-20240620',
            'litellm_params': {
                'model': 'azure/claude-3-5-sonnet-20240620',
                'api_key': 'AZURE_API_KEY',
                'api_base': 'https://MODEL-URL.openai.azure.com//openai/',
                'api_version': '2023-05-15',
                'max_retries': 7,
                'timeout': 0.01,
                'stream_timeout': 0.000_001,
            },
            'tpm': 100000,
            'rpm': 10000,
        },
    ]
    return LLMConfig(
        model='gpt-4o',
        api_key='dummy_default_key',
        router_models=model_list,
        router_routing_strategy='simple-shuffle',
        router_num_retries=3,
        router_cooldown_time=1.0,
        router_allowed_fails=5,
        router_cache_responses=False,
        router_options={
            'set_verbose': True,
            'debug_level': 1,
            'default_litellm_params': {},
            'timeout': 30,
        },
    )


def test_llm_init_with_default_config(default_config):
    llm = LLM(default_config)
    assert llm.config.model == 'openai/gpt-4o'
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
    llm = LLM(LLMConfig(model='openai/gpt-4o-mini', api_key='test_key'))
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


######################################################################################
# Tests involving completion and retries
######################################################################################


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
        (
            APIConnectionError,
            {'llm_provider': 'test_provider', 'model': 'test_model'},
            2,
        ),
        (
            InternalServerError,
            {'llm_provider': 'test_provider', 'model': 'test_model'},
            2,
        ),
        (
            ServiceUnavailableError,
            {'llm_provider': 'test_provider', 'model': 'test_model'},
            2,
        ),
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
def test_completion_exhausts_retries(mock_litellm_completion, default_config):
    mock_litellm_completion.side_effect = APIConnectionError(
        'Persistent error', llm_provider='test_provider', model='test_model'
    )

    llm = LLM(config=default_config)
    with pytest.raises(APIConnectionError):
        llm.completion(
            messages=[{'role': 'user', 'content': 'Hello!'}],
            stream=False,
        )

    assert mock_litellm_completion.call_count == llm.config.num_retries


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


######################################################################################
#################################### Router tests ####################################
######################################################################################


@patch('openhands.llm.llm.litellm.Router')
@patch('openhands.llm.llm.litellm_completion')
def test_router_completion_with_fallback(
    mock_litellm_completion, mock_router, router_config
):
    # Mock the router's completion method to raise an exception
    mock_router_instance = MagicMock()
    mock_router_instance.completion.side_effect = APIConnectionError(
        'Router error', llm_provider='test_provider', model='test_model'
    )
    mock_router.return_value = mock_router_instance

    # Mock the litellm_completion method to return a fallback response
    mock_litellm_completion.return_value = {
        'choices': [{'message': {'content': 'Fallback response'}}]
    }

    llm = LLM(router_config)

    response = llm._router_completion_with_fallback(
        messages=[{'role': 'user', 'content': 'Hello!'}]
    )

    # Check if the router's completion method was called
    mock_router_instance.completion.assert_called_once_with(
        messages=[{'role': 'user', 'content': 'Hello!'}]
    )

    # Check if the litellm_completion method was called as a fallback
    mock_litellm_completion.assert_called_once_with(
        model=router_config.model, messages=[{'role': 'user', 'content': 'Hello!'}]
    )

    # Check the response
    assert response['choices'][0]['message']['content'] == 'Fallback response'


# credits go to the litellm project for the below tests


@patch('openhands.llm.llm.litellm.Router')
def test_llm_init_with_router(mock_router, router_config):
    llm = LLM(router_config)

    # Check if Router was initialized with correct parameters
    mock_router.assert_called_once()
    router_args = mock_router.call_args[1]
    assert router_args['model_list'] == router_config.router_models
    assert router_args['routing_strategy'] == router_config.router_routing_strategy
    assert router_args['num_retries'] == router_config.router_num_retries
    assert router_args['cooldown_time'] == router_config.router_cooldown_time
    assert router_args['allowed_fails'] == router_config.router_allowed_fails
    assert router_args['cache_responses'] == router_config.router_cache_responses
    assert router_args['set_verbose'] == router_config.router_options['set_verbose']
    assert router_args['debug_level'] == router_config.router_options['debug_level']

    # Check if the router attribute is set
    assert hasattr(llm, 'router')
    assert isinstance(llm.router, MagicMock)


@patch('openhands.llm.llm.litellm.Router')
def test_llm_completion_with_router(mock_router, router_config):
    # Mock the router's completion method
    mock_router_instance = MagicMock()
    mock_router_instance.completion.return_value = {
        'choices': [{'message': {'content': 'Router response'}}]
    }
    mock_router.return_value = mock_router_instance

    llm = LLM(router_config)
    response = llm.completion(messages=[{'role': 'user', 'content': 'Hello!'}])

    # Check if the router's completion method was called
    mock_router_instance.completion.assert_called_once_with(
        messages=[{'role': 'user', 'content': 'Hello!'}]
    )

    # Check the response
    assert response['choices'][0]['message']['content'] == 'Router response'


@patch('openhands.llm.llm.litellm.Router')
@patch('openhands.llm.llm.litellm_completion')
def test_llm_completion_with_router_no_model(
    mock_litellm_completion, mock_router, router_config
):
    # Remove the router_models from the config
    router_config.router_models = []

    # Mock the router's completion method
    mock_router_instance = MagicMock()
    mock_router_instance.completion.return_value = {
        'choices': [{'message': {'content': 'Router response'}}]
    }
    mock_router.return_value = mock_router_instance

    # Mock the litellm_completion method
    mock_litellm_completion.return_value = {
        'choices': [{'message': {'content': 'Fallback response'}}]
    }

    # Create the LLM instance
    llm = LLM(router_config)

    # Call the completion method
    response = llm.completion(messages=[{'role': 'user', 'content': 'Hello!'}])

    # Check if the litellm_completion method was called with the default model
    mock_litellm_completion.assert_called_once_with(
        model=router_config.model,
        api_key=router_config.api_key,
        temperature=router_config.temperature,
        top_p=router_config.top_p,
        drop_params=router_config.drop_params,
        max_tokens=4096,  # This is the default value set in the LLM class
        messages=[{'role': 'user', 'content': 'Hello!'}],
    )

    # Check the response
    assert response['choices'][0]['message']['content'] == 'Fallback response'


@patch('openhands.llm.llm.litellm.Router')
def test_router_init_gpt_4_vision_enhancements(mock_router):
    router_config = LLMConfig(
        model='gpt-4-vision-enhanced',
        api_key='dummy_default_key',
        router_models=[
            {
                'model_name': 'gpt-4-vision-enhancements',
                'litellm_params': {
                    'model': 'azure/gpt-4-vision',
                    'api_key': 'AZURE_API_KEY',
                    'base_url': 'https://gpt-4-vision-resource.openai.azure.com/openai/deployments/gpt-4-vision/extensions/',
                    'dataSources': [
                        {
                            'type': 'AzureComputerVision',
                            'parameters': {
                                'endpoint': 'AZURE_VISION_ENHANCE_ENDPOINT',
                                'key': 'AZURE_VISION_ENHANCE_KEY',
                            },
                        }
                    ],
                },
            }
        ],
        router_routing_strategy='simple-shuffle',
        router_num_retries=3,
        router_cooldown_time=1.0,
        router_allowed_fails=5,
        router_cache_responses=False,
        router_options={
            'set_verbose': True,
            'debug_level': 1,
            'default_litellm_params': {},
            'timeout': 30,
        },
    )

    llm = LLM(router_config)

    # Check if Router was initialized with correct parameters
    mock_router.assert_called_once()
    router_args = mock_router.call_args[1]
    assert router_args['model_list'] == router_config.router_models
    assert router_args['routing_strategy'] == router_config.router_routing_strategy
    assert router_args['num_retries'] == router_config.router_num_retries
    assert router_args['cooldown_time'] == router_config.router_cooldown_time
    assert router_args['allowed_fails'] == router_config.router_allowed_fails
    assert router_args['cache_responses'] == router_config.router_cache_responses
    assert router_args['set_verbose'] == router_config.router_options['set_verbose']
    assert router_args['debug_level'] == router_config.router_options['debug_level']

    # Check if the router attribute is set
    assert hasattr(llm, 'router')
    assert isinstance(llm.router, MagicMock)


@patch('openhands.llm.llm.litellm.Router')
def test_llm_init_with_toml_config(mock_router):
    # Mock TOML configuration
    toml_config = """
model = "gpt-4-vision-enhanced"
api_key = "dummy_default_key"

[[router_models]]
model_name = "gpt-4-vision-enhancements"
[router_models.litellm_params]
model = "azure/gpt-4-vision"
api_key = "AZURE_API_KEY"
base_url = "https://gpt-4-vision-resource.openai.azure.com/openai/deployments/gpt-4-vision/extensions/"

[[router_models.litellm_params.dataSources]]
type = "AzureComputerVision"

[router_models.litellm_params.dataSources.parameters]
endpoint = "AZURE_VISION_ENHANCE_ENDPOINT"
key = "AZURE_VISION_ENHANCE_KEY"

[router_options]
set_verbose = true
debug_level = 1
timeout = 30

router_routing_strategy = "simple-shuffle"
router_num_retries = 3
router_cooldown_time = 1.0
router_allowed_fails = 5
router_cache_responses = false
    """

    # Parse the TOML configuration
    config_data = toml.loads(toml_config)

    # Initialize LLMConfig with the parsed data
    router_config = LLMConfig(
        model=config_data.get('model', 'default_model'),
        api_key=config_data.get('api_key', 'default_api_key'),
        router_models=config_data.get('router_models', []),
        router_routing_strategy=config_data.get(
            'router_routing_strategy', 'default_strategy'
        ),
        router_num_retries=config_data.get('router_num_retries', 3),
        router_cooldown_time=config_data.get('router_cooldown_time', 1.0),
        router_allowed_fails=config_data.get('router_allowed_fails', 5),
        router_cache_responses=config_data.get('router_cache_responses', False),
        router_options=config_data.get('router_options', {}),
    )

    llm = LLM(router_config)

    # Check if Router was initialized with correct parameters
    mock_router.assert_called_once()
    router_args = mock_router.call_args[1]
    assert router_args['model_list'] == router_config.router_models
    assert router_args['routing_strategy'] == router_config.router_routing_strategy
    assert router_args['num_retries'] == router_config.router_num_retries
    assert router_args['cooldown_time'] == router_config.router_cooldown_time
    assert router_args['allowed_fails'] == router_config.router_allowed_fails
    assert router_args['cache_responses'] == router_config.router_cache_responses
    assert router_args['set_verbose'] == router_config.router_options['set_verbose']
    assert router_args['debug_level'] == router_config.router_options['debug_level']

    # Check if the router attribute is set
    assert hasattr(llm, 'router')
    assert isinstance(llm.router, MagicMock)


@pytest.fixture
def router_with_fallbacks_config():
    return LLMConfig(
        model='bad-model',
        api_key='dummy_default_key',
        router_models=[
            {
                'model_name': 'bad-model',
                'litellm_params': {
                    'model': 'openai/my-bad-model',
                    'api_key': 'my-bad-api-key',
                },
            },
            {
                'model_name': 'my-good-model',
                'litellm_params': {
                    'model': 'gpt-4o',
                    'api_key': 'OPENAI_API_KEY',
                },
            },
        ],
        router_routing_strategy='simple-shuffle',
        router_num_retries=3,
        router_cooldown_time=1.0,
        router_allowed_fails=5,
        router_cache_responses=False,
        router_options={
            'set_verbose': True,
            'debug_level': 1,
            'timeout': 30,
        },
    )


@patch('openhands.llm.llm.litellm.Router')
def test_client_side_fallbacks_list(mock_router, router_with_fallbacks_config):
    mock_router_instance = MagicMock()
    mock_router_instance.completion.return_value = {
        'choices': [{'message': {'content': 'Hey! nice day'}}]
    }
    mock_router.return_value = mock_router_instance

    llm = LLM(router_with_fallbacks_config)

    response = llm.completion(
        messages=[{'role': 'user', 'content': "Hey, how's it going?"}],
        fallbacks=['my-good-model'],
        mock_testing_fallbacks=True,
        mock_response='Hey! nice day',
    )

    assert response['choices'][0]['message']['content'] == 'Hey! nice day'
    assert mock_router_instance.completion.call_count == 1


@pytest.fixture
def router_content_policy_config():
    return LLMConfig(
        model='content-policy-model',
        api_key='dummy_default_key',
        router_models=[
            {
                'model_name': 'content-policy-model',
                'litellm_params': {
                    'model': 'openai/content-policy-model',
                    'api_key': 'content-policy-api-key',
                },
            },
            {
                'model_name': 'fallback-model',
                'litellm_params': {
                    'model': 'gpt-4o',
                    'api_key': 'OPENAI_API_KEY',
                },
            },
        ],
        router_routing_strategy='simple-shuffle',
        router_num_retries=3,
        router_cooldown_time=1.0,
        router_allowed_fails=5,
        router_cache_responses=False,
        router_options={
            'set_verbose': True,
            'debug_level': 1,
            'timeout': 30,
        },
    )


@patch('openhands.llm.llm.litellm.Router')
def test_router_content_policy_fallbacks(mock_router, router_content_policy_config):
    mock_router_instance = MagicMock()
    mock_router_instance.completion.return_value = {
        'choices': [{'message': {'content': 'Content policy fallback response'}}]
    }
    mock_router.return_value = mock_router_instance

    llm = LLM(router_content_policy_config)

    response = llm.completion(
        messages=[{'role': 'user', 'content': 'Test content policy'}],
        fallbacks=['fallback-model'],
        mock_testing_fallbacks=True,
        mock_response='Content policy fallback response',
    )

    assert (
        response['choices'][0]['message']['content']
        == 'Content policy fallback response'
    )
    assert mock_router_instance.completion.call_count == 1
