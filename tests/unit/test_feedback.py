import pytest
from fastapi import Request
from fastapi.responses import JSONResponse

from openhands.core.config.app_config import AppConfig
from openhands.core.config.llm_config import LLMConfig
from openhands.core.config.agent_config import AgentConfig
from openhands.events.stream import EventStream
from openhands.server.data_models.feedback import FeedbackDataModel
from openhands.server.routes.feedback import submit_feedback
from openhands.server.session.conversation import Conversation
from openhands.storage.memory import InMemoryFileStore


class MockConversation:
    def __init__(self, config: AppConfig, event_stream: EventStream):
        self.config = config
        self.event_stream = event_stream


class MockRequest:
    def __init__(self, body: dict, conversation: MockConversation):
        self.body = body
        self.state = type('State', (), {'conversation': conversation})

    async def json(self):
        return self.body


@pytest.mark.asyncio
async def test_submit_feedback_includes_model_agent_info(mocker):
    # Mock the store_feedback function
    mock_store_feedback = mocker.patch(
        'openhands.server.routes.feedback.store_feedback',
        return_value={'message': 'Success', 'feedback_id': '123', 'password': 'pass'},
    )

    # Create a mock config with model and agent info
    config = AppConfig()
    config.llms['llm'] = LLMConfig(model='gpt-4', custom_llm_provider='openai')
    config.agents['test-agent'] = AgentConfig()
    config.default_agent = 'test-agent'

    # Create a mock event stream
    event_stream = EventStream('test-sid', InMemoryFileStore())

    # Create a mock conversation
    conversation = MockConversation(config, event_stream)

    # Create a mock request
    request = MockRequest(
        {
            'email': 'test@example.com',
            'version': '1.0',
            'permissions': 'private',
            'polarity': 'positive',
        },
        conversation,
    )

    # Call submit_feedback
    response = await submit_feedback(request)

    # Verify the response
    assert isinstance(response, JSONResponse)
    assert response.status_code == 200

    # Verify store_feedback was called with correct data
    mock_store_feedback.assert_called_once()
    feedback_model: FeedbackDataModel = mock_store_feedback.call_args[0][0]
    assert feedback_model.model == 'gpt-4'
    assert feedback_model.provider == 'openai'
    assert feedback_model.agent == 'test-agent'
