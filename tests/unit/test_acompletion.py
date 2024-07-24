from unittest.mock import patch

import pytest

from opendevin.core.config import config
from opendevin.llm.llm import LLM

# from opendevin.core.config import AppConfig


@pytest.fixture
def test_llm():
    # Create a mock config for testing
    llm = LLM(config=config.get_llm_config())
    # config = AppConfig()
    # config.model = 'gpt-3.5-turbo'
    # config.base_url = 'https://api.openai.com/v1'
    # config.api_key = 'test-api-key'
    # config.api_version = '2024-02-15'
    return llm


@pytest.fixture
def mock_response():
    return [
        {'choices': [{'delta': {'content': 'This is a'}}]},
        {'choices': [{'delta': {'content': ' test'}}]},
        {'choices': [{'delta': {'content': ' message.'}}]},
        {'choices': [{'delta': {'content': ' It is'}}]},
        {'choices': [{'delta': {'content': ' a bit'}}]},
        {'choices': [{'delta': {'content': ' longer'}}]},
        {'choices': [{'delta': {'content': ' than'}}]},
        {'choices': [{'delta': {'content': ' the'}}]},
        {'choices': [{'delta': {'content': ' previous'}}]},
        {'choices': [{'delta': {'content': ' one,'}}]},
        {'choices': [{'delta': {'content': ' but'}}]},
        {'choices': [{'delta': {'content': ' hopefully'}}]},
        {'choices': [{'delta': {'content': ' still'}}]},
        {'choices': [{'delta': {'content': ' short'}}]},
        {'choices': [{'delta': {'content': ' enough.'}}]},
    ]


@pytest.mark.asyncio
async def test_acompletion_non_streaming():
    with patch.object(LLM, '_call_acompletion') as mock_call_acompletion:
        mock_response = {
            'choices': [{'message': {'content': 'This is a test message.'}}]
        }
        mock_call_acompletion.return_value = mock_response
        test_llm = LLM(config=config.get_llm_config())
        response = await test_llm.async_completion(
            messages=[{'role': 'user', 'content': 'Hello!'}],
            stream=False,
            drop_params=True,
        )
        # Assertions for non-streaming completion
        assert response['choices'][0]['message']['content'] != ''


@pytest.mark.asyncio
async def test_acompletion_streaming(mock_response):
    with patch.object(LLM, '_call_acompletion') as mock_call_acompletion:
        mock_call_acompletion.return_value.__aiter__.return_value = iter(mock_response)
        test_llm = LLM(config=config.get_llm_config())
        async for chunk in test_llm.async_streaming_completion(
            messages=[{'role': 'user', 'content': 'Hello!'}], stream=True
        ):
            print(f"Chunk: {chunk['choices'][0]['delta']['content']}")
            # Assertions for streaming completion
            assert chunk['choices'][0]['delta']['content'] in [
                r['choices'][0]['delta']['content'] for r in mock_response
            ]


@pytest.mark.asyncio
async def test_completion(test_llm):
    with patch.object(LLM, 'completion') as mock_completion:
        mock_completion.return_value = {
            'choices': [{'message': {'content': 'This is a test message.'}}]
        }
        response = test_llm.completion(messages=[{'role': 'user', 'content': 'Hello!'}])
        assert response['choices'][0]['message']['content'] == 'This is a test message.'
