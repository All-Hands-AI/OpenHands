import pytest
from unittest.mock import MagicMock, patch

from openhands.core.config import AppConfig
from openhands.events.action import MessageAction
from openhands.events.observation import NullObservation
from openhands.server.session.conversation import Conversation
from openhands.storage.memory import InMemoryFileStore


@pytest.fixture
def conversation():
    config = AppConfig()
    file_store = InMemoryFileStore()
    with patch("openhands.runtime.impl.eventstream.eventstream_runtime.docker") as mock_docker:
        mock_client = MagicMock()
        mock_client.version.return_value = {"Version": "20.10.0"}
        mock_docker.from_env.return_value = mock_client
        return Conversation("test_sid", file_store, config)


def test_summarize_actions(conversation):
    # Mock the event stream
    conversation.event_stream.get_events = MagicMock(return_value=[
        MessageAction("Hello"),
        NullObservation(content="Hi there"),
        MessageAction("Fix the bug"),
        NullObservation(content="I'll help fix the bug"),
    ])

    # Mock the LLM
    with patch("openhands.memory.condenser.LLM") as mock_llm:
        mock_llm.completion.return_value = {
            "choices": [{"message": {"content": "fixing-bug-in-code"}}]
        }
        summary = conversation.summarize_actions(mock_llm)
        assert summary == "fixing-bug-in-code"

        # Verify the prompt sent to the LLM
        messages = mock_llm.completion.call_args[1]["messages"]
        assert len(messages) == 1
        assert messages[0]["role"] == "user"
        assert "Please summarize" in messages[0]["content"]
