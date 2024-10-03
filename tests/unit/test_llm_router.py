
import pytest
from unittest.mock import Mock, patch
from openhands.core.config import LLMConfig
from openhands.core.message import Message
from openhands.llm.llm import LLM
from openhands.llm.llm_router import LLMRouter

@pytest.fixture
def mock_notdiamond():
    with patch('openhands.llm.llm_router.NotDiamond') as mock:
        yield mock

def test_llm_router_enabled(mock_notdiamond):
    config = LLMConfig(
        model="test-model",
        llm_router_enabled=True,
        llm_providers=["model1", "model2"]
    )
    llm = LLM(config)

    assert isinstance(llm.router, LLMRouter)

    messages = [Message(role="user", content="Hello")]
    mock_response = Mock()
    mock_response.choices[0].message.content = "Hello, how can I help you?"
    llm.router.complete = Mock(return_value=(mock_response, 0.5))

    response, latency = llm.complete(messages)

    assert response == "Hello, how can I help you?"
    assert isinstance(latency, float)
    llm.router.complete.assert_called_once_with(messages)

def test_llm_router_disabled():
    config = LLMConfig(
        model="test-model",
        llm_router_enabled=False
    )
    llm = LLM(config)

    assert llm.router is None

    messages = [Message(role="user", content="Hello")]
    with patch.object(llm, '_completion') as mock_completion:
        mock_response = Mock()
        mock_response.choices[0].message.content = "Hello, how can I help you?"
        mock_completion.return_value = mock_response

        response, latency = llm.complete(messages)

    assert response == "Hello, how can I help you?"
    assert isinstance(latency, float)
    mock_completion.assert_called_once()
