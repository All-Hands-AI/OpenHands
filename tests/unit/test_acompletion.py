import asyncio
from contextlib import contextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from openhands.core.config import load_openhands_config
from openhands.core.exceptions import UserCancelledError
from openhands.llm.async_llm import AsyncLLM
from openhands.llm.llm import LLM
from openhands.llm.streaming_llm import StreamingLLM

config = load_openhands_config()


@pytest.fixture
def test_llm():
    return _get_llm(LLM)


def _get_llm(type_: type[LLM]):
    with _patch_http():
        return type_(config=config.get_llm_config())


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


@contextmanager
def _patch_http():
    with patch('openhands.llm.llm.httpx.get', MagicMock()) as mock_http:
        mock_http.json.return_value = {
            'data': [
                {'model_name': 'some_model'},
                {'model_name': 'another_model'},
            ]
        }
        yield


@pytest.mark.asyncio
async def test_acompletion_non_streaming():
    with patch.object(AsyncLLM, '_call_acompletion') as mock_call_acompletion:
        mock_response = {
            'choices': [{'message': {'content': 'This is a test message.'}}]
        }
        mock_call_acompletion.return_value = mock_response
        test_llm = _get_llm(AsyncLLM)
        response = await test_llm.async_completion(
            messages=[{'role': 'user', 'content': 'Hello!'}],
            stream=False,
            drop_params=True,
        )
        # Assertions for non-streaming completion
        assert response['choices'][0]['message']['content'] != ''


@pytest.mark.asyncio
async def test_acompletion_streaming(mock_response):
    with patch.object(StreamingLLM, '_call_acompletion') as mock_call_acompletion:
        mock_call_acompletion.return_value.__aiter__.return_value = iter(mock_response)
        test_llm = _get_llm(StreamingLLM)
        async for chunk in test_llm.async_streaming_completion(
            messages=[{'role': 'user', 'content': 'Hello!'}], stream=True
        ):
            print(f'Chunk: {chunk["choices"][0]["delta"]["content"]}')
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


@pytest.mark.asyncio
@pytest.mark.parametrize('cancel_delay', [0.1, 0.3, 0.5, 0.7, 0.9])
async def test_async_completion_with_user_cancellation(cancel_delay):
    cancel_event = asyncio.Event()

    async def mock_on_cancel_requested():
        is_set = cancel_event.is_set()
        print(f'Cancel requested: {is_set}')
        return is_set

    async def mock_acompletion(*args, **kwargs):
        print('Starting mock_acompletion')
        for i in range(20):  # Increased iterations for longer running task
            print(f'mock_acompletion iteration {i}')
            await asyncio.sleep(0.1)
            if await mock_on_cancel_requested():
                print('Cancellation detected in mock_acompletion')
                raise UserCancelledError('LLM request cancelled by user')
        print('Completing mock_acompletion without cancellation')
        return {'choices': [{'message': {'content': 'This is a test message.'}}]}

    with patch.object(
        AsyncLLM, '_call_acompletion', new_callable=AsyncMock
    ) as mock_call_acompletion:
        mock_call_acompletion.side_effect = mock_acompletion
        test_llm = _get_llm(AsyncLLM)

        async def cancel_after_delay():
            print(f'Starting cancel_after_delay with delay {cancel_delay}')
            await asyncio.sleep(cancel_delay)
            print('Setting cancel event')
            cancel_event.set()

        with pytest.raises(UserCancelledError):
            await asyncio.gather(
                test_llm.async_completion(
                    messages=[{'role': 'user', 'content': 'Hello!'}],
                    stream=False,
                ),
                cancel_after_delay(),
            )

    # Ensure the mock was called
    mock_call_acompletion.assert_called_once()


@pytest.mark.asyncio
@pytest.mark.parametrize('cancel_after_chunks', [1, 3, 5, 7, 9])
async def test_async_streaming_completion_with_user_cancellation(cancel_after_chunks):
    cancel_requested = False

    test_messages = [
        'This is ',
        'a test ',
        'message ',
        'with ',
        'multiple ',
        'chunks ',
        'to ',
        'simulate ',
        'a ',
        'longer ',
        'streaming ',
        'response.',
    ]

    async def mock_acompletion(*args, **kwargs):
        for i, content in enumerate(test_messages):
            yield {'choices': [{'delta': {'content': content}}]}
            if i + 1 == cancel_after_chunks:
                nonlocal cancel_requested
                cancel_requested = True
            if cancel_requested:
                raise UserCancelledError('LLM request cancelled by user')
            await asyncio.sleep(0.05)  # Simulate some delay between chunks

    with patch.object(
        AsyncLLM, '_call_acompletion', new_callable=AsyncMock
    ) as mock_call_acompletion:
        mock_call_acompletion.return_value = mock_acompletion()
        test_llm = _get_llm(StreamingLLM)

        received_chunks = []
        with pytest.raises(UserCancelledError):
            async for chunk in test_llm.async_streaming_completion(
                messages=[{'role': 'user', 'content': 'Hello!'}], stream=True
            ):
                received_chunks.append(chunk['choices'][0]['delta']['content'])
                print(f'Chunk: {chunk["choices"][0]["delta"]["content"]}')

        # Assert that we received the expected number of chunks before cancellation
        assert len(received_chunks) == cancel_after_chunks
        assert received_chunks == test_messages[:cancel_after_chunks]

    # Ensure the mock was called
    mock_call_acompletion.assert_called_once()
