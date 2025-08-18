from unittest.mock import ANY, AsyncMock, patch

import pytest
from litellm.exceptions import (
    RateLimitError,
)

from openhands.core.config.llm_config import LLMConfig
from openhands.core.config.openhands_config import OpenHandsConfig
from openhands.llm.llm_registry import LLMRegistry
from openhands.runtime.runtime_status import RuntimeStatus
from openhands.server.services.conversation_stats import ConversationStats
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
    config = OpenHandsConfig()
    return LLMRegistry(config=config)


@pytest.fixture
def conversation_stats():
    file_store = InMemoryFileStore({})
    return ConversationStats(
        file_store=file_store, conversation_id='test-conversation', user_id='test-user'
    )


@pytest.mark.asyncio
@patch('openhands.llm.llm.litellm_completion')
async def test_notify_on_llm_retry(
    mock_litellm_completion,
    mock_sio,
    default_llm_config,
    llm_registry,
    conversation_stats,
):
    config = OpenHandsConfig()
    config.set_llm_config(default_llm_config)
    session = Session(
        sid='..sid..',
        file_store=InMemoryFileStore({}),
        config=config,
        llm_registry=llm_registry,
        convo_stats=conversation_stats,
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

        # Set the retry listener on the registry
        llm_registry.retry_listner = session._notify_on_llm_retry

        # Create an LLM through the registry
        llm = llm_registry.get_llm(
            service_id='test_service',
            config=default_llm_config,
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
