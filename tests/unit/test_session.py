from unittest.mock import ANY, AsyncMock, patch

import pytest
from litellm.exceptions import (
    RateLimitError,
)

from openhands.core.config.llm_config import LLMConfig
from openhands.core.config.openhands_config import OpenHandsConfig
from openhands.llm.metrics_registry import LLMRegistry
from openhands.runtime.runtime_status import RuntimeStatus
from openhands.server.session.session import Session
from openhands.storage.memory import InMemoryFileStore


@pytest.fixture
def mock_status_callback():
    return AsyncMock()


@pytest.fixture
def mock_sio():
    return AsyncMock()


@pytest.fixture
def default_llm_config():
    return LLMConfig(
        model='gpt-4o',
        api_key='test_key',
        num_retries=2,
        retry_min_wait=1,
        retry_max_wait=2,
    )


@pytest.fixture
def llm_registry():
    file_store = InMemoryFileStore({})
    return LLMRegistry(
        file_store=file_store, conversation_id='test-conversation', user_id='test-user'
    )


@pytest.mark.asyncio
@patch('openhands.llm.llm.litellm_completion')
async def test_notify_on_llm_retry(
    mock_litellm_completion, mock_sio, default_llm_config, llm_registry
):
    config = OpenHandsConfig()
    config.set_llm_config(default_llm_config)
    session = Session(
        sid='..sid..',
        file_store=InMemoryFileStore({}),
        config=config,
        llm_registry=llm_registry,
        sio=mock_sio,
        user_id='..uid..',
    )
    session.queue_status_message = AsyncMock()

    with patch('time.sleep') as _mock_sleep:
        mock_litellm_completion.side_effect = [
            RateLimitError(
                'Rate limit exceeded', llm_provider='test_provider', model='test_model'
            ),
            {'choices': [{'message': {'content': 'Retry successful'}}]},
        ]

        # Create an LLM through the registry with the session's retry listener
        llm = llm_registry.register_llm(
            service_id='test_service',
            config=default_llm_config,
            retry_listener=session._notify_on_llm_retry,
        )

        llm.completion(
            messages=[{'role': 'user', 'content': 'Hello!'}],
            stream=False,
        )

    assert mock_litellm_completion.call_count == 2
    session.queue_status_message.assert_called_once_with(
        'info', RuntimeStatus.LLM_RETRY, ANY
    )
    await session.close()
