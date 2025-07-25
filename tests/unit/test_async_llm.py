from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from openhands.core.config import LLMConfig
from openhands.core.exceptions import LLMNoResponseError
from openhands.llm.async_llm import AsyncLLM


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
def mock_logger(monkeypatch):
    # suppress logging of completion data to file
    mock_logger = MagicMock()
    monkeypatch.setattr('openhands.llm.debug_mixin.llm_prompt_logger', mock_logger)
    monkeypatch.setattr('openhands.llm.debug_mixin.llm_response_logger', mock_logger)
    monkeypatch.setattr('openhands.llm.async_llm.logger', mock_logger)
    return mock_logger


@pytest.mark.asyncio
async def test_async_llm_init(default_config):
    """Test that AsyncLLM initializes correctly with default config."""
    llm = AsyncLLM(default_config)
    assert llm.config.model == 'gpt-4o'
    assert llm.config.api_key.get_secret_value() == 'test_key'
    assert callable(llm.async_completion)


@pytest.mark.asyncio
async def test_async_completion_basic(default_config, mock_logger):
    """Test basic async completion functionality."""
    with patch(
        'openhands.llm.async_llm.litellm_acompletion', new_callable=AsyncMock
    ) as mock_acompletion:
        mock_acompletion.return_value = {
            'id': 'test-response-id',
            'choices': [{'message': {'content': 'Test response'}}],
            'usage': {'prompt_tokens': 10, 'completion_tokens': 5, 'total_tokens': 15},
        }

        llm = AsyncLLM(default_config)
        response = await llm.async_completion(
            messages=[{'role': 'user', 'content': 'Hello!'}]
        )

        assert response['choices'][0]['message']['content'] == 'Test response'
        assert mock_acompletion.call_count == 1

        # Verify metrics were updated
        assert len(llm.metrics.token_usages) == 1
        assert llm.metrics.token_usages[0].prompt_tokens == 10
        assert llm.metrics.token_usages[0].completion_tokens == 5


@pytest.mark.asyncio
async def test_async_completion_with_function_calling(default_config):
    """Test that function calling works correctly in AsyncLLM."""
    with (
        patch(
            'openhands.llm.async_llm.litellm_acompletion', new_callable=AsyncMock
        ) as mock_acompletion,
        patch.object(AsyncLLM, 'is_function_calling_active', return_value=True),
    ):
        # Mock a function call response
        mock_acompletion.return_value = {
            'id': 'test-response-id',
            'choices': [
                {
                    'message': {
                        'content': None,
                        'tool_calls': [
                            {
                                'function': {
                                    'name': 'test_function',
                                    'arguments': '{"arg1": "value1", "arg2": "value2"}',
                                },
                                'id': 'call_123',
                            }
                        ],
                    }
                }
            ],
            'usage': {'prompt_tokens': 15, 'completion_tokens': 10, 'total_tokens': 25},
        }

        # Set model to one that supports function calling
        config = LLMConfig(model='claude-3-5-sonnet-20240620', api_key='test_key')

        llm = AsyncLLM(config)

        # Define a test tool
        test_tool = {
            'type': 'function',
            'function': {
                'name': 'test_function',
                'description': 'A test function',
                'parameters': {
                    'type': 'object',
                    'properties': {
                        'arg1': {'type': 'string'},
                        'arg2': {'type': 'string'},
                    },
                    'required': ['arg1', 'arg2'],
                },
            },
        }

        await llm.async_completion(
            messages=[{'role': 'user', 'content': 'Call the test function'}],
            tools=[test_tool],
            tool_choice='auto',
        )

        # Verify the API was called correctly
        assert mock_acompletion.call_count == 1
        # Verify the tools were passed correctly
        kwargs = mock_acompletion.call_args[1]
        assert 'tools' in kwargs
        assert kwargs['tools'][0]['function']['name'] == 'test_function'


@pytest.mark.asyncio
async def test_async_completion_with_mock_function_calling(default_config):
    """Test that function calling mocking works correctly for models that don't support it natively."""
    with patch(
        'openhands.llm.async_llm.litellm_acompletion', new_callable=AsyncMock
    ) as mock_acompletion:
        # Mock a text response that will be converted to a function call
        mock_acompletion.return_value = {
            'id': 'test-response-id',
            'choices': [
                {
                    'message': {
                        'content': 'I need to call test_function with arg1="value1" and arg2="value2"',
                        'role': 'assistant',
                    }
                }
            ],
            'usage': {'prompt_tokens': 20, 'completion_tokens': 15, 'total_tokens': 35},
        }

        # Use a model that doesn't support function calling
        config = LLMConfig(
            model='some-model-without-function-calling', api_key='test_key'
        )

        llm = AsyncLLM(config)

        # Define a test tool
        test_tool = {
            'type': 'function',
            'function': {
                'name': 'test_function',
                'description': 'A test function',
                'parameters': {
                    'type': 'object',
                    'properties': {
                        'arg1': {'type': 'string'},
                        'arg2': {'type': 'string'},
                    },
                    'required': ['arg1', 'arg2'],
                },
            },
        }

        # Patch the is_function_calling_active method to return False
        # and patch the convert_fncall_messages_to_non_fncall_messages function
        with (
            patch.object(AsyncLLM, 'is_function_calling_active', return_value=False),
            patch(
                'openhands.llm.async_llm.convert_fncall_messages_to_non_fncall_messages'
            ) as mock_convert_to_non_fncall,
            patch(
                'openhands.llm.async_llm.convert_non_fncall_messages_to_fncall_messages'
            ) as mock_convert_to_fncall,
        ):
            # Set up the mocks
            mock_convert_to_non_fncall.return_value = [
                {'role': 'user', 'content': 'Call the test function (converted)'}
            ]
            mock_convert_to_fncall.return_value = [
                {'role': 'user', 'content': 'Call the test function'},
                {
                    'role': 'assistant',
                    'content': None,
                    'tool_calls': [
                        {
                            'function': {
                                'name': 'test_function',
                                'arguments': '{"arg1": "value1", "arg2": "value2"}',
                            },
                            'id': 'call_123',
                        }
                    ],
                },
            ]

            await llm.async_completion(
                messages=[{'role': 'user', 'content': 'Call the test function'}],
                tools=[test_tool],
                tool_choice='auto',
            )

            # Verify the conversion functions were called
            mock_convert_to_non_fncall.assert_called_once()
            # Verify the API was called correctly
            assert mock_acompletion.call_count == 1


@pytest.mark.asyncio
async def test_async_completion_with_retry(default_config):
    """Test that retries work correctly in AsyncLLM."""
    with patch(
        'openhands.llm.async_llm.litellm_acompletion', new_callable=AsyncMock
    ) as mock_acompletion:
        # First call raises an error, second call succeeds
        mock_acompletion.side_effect = [
            LLMNoResponseError('No response from LLM'),
            {
                'id': 'test-retry-id',
                'choices': [{'message': {'content': 'Retry successful'}}],
                'usage': {
                    'prompt_tokens': 10,
                    'completion_tokens': 5,
                    'total_tokens': 15,
                },
            },
        ]

        llm = AsyncLLM(default_config)
        response = await llm.async_completion(
            messages=[{'role': 'user', 'content': 'Hello!'}]
        )

        assert response['choices'][0]['message']['content'] == 'Retry successful'
        assert mock_acompletion.call_count == 2


@pytest.mark.asyncio
async def test_async_completion_with_logging(default_config):
    """Test that completion logging works correctly in AsyncLLM."""
    with (
        patch(
            'openhands.llm.async_llm.litellm_acompletion', new_callable=AsyncMock
        ) as mock_acompletion,
        patch('openhands.llm.async_llm.open', MagicMock()) as mock_open,
        patch('openhands.io.json.dumps') as mock_json_dumps,
    ):
        mock_acompletion.return_value = {
            'id': 'test-log-id',
            'choices': [{'message': {'content': 'Test logging'}}],
            'usage': {'prompt_tokens': 10, 'completion_tokens': 5, 'total_tokens': 15},
        }

        # Create a temp directory for logs
        with patch('os.makedirs') as mock_makedirs:
            log_dir = '/tmp/llm_logs'
            config = LLMConfig(
                model='gpt-4o',
                api_key='test_key',
                log_completions=True,
                log_completions_folder=log_dir,
            )

            llm = AsyncLLM(config)
            response = await llm.async_completion(
                messages=[{'role': 'user', 'content': 'Hello!'}]
            )

            assert response['choices'][0]['message']['content'] == 'Test logging'
            mock_makedirs.assert_called_once_with(log_dir, exist_ok=True)
            mock_open.assert_called_once()
            # We don't check the exact number of calls to json.dumps as it might be called multiple times
            assert mock_json_dumps.call_count >= 1
