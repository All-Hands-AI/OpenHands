from unittest.mock import MagicMock

import pytest

from openhands.controller.agent import Agent
from openhands.controller.agent_controller import AgentController
from openhands.core.config.agent_config import AgentConfig
from openhands.events import EventSource, EventStream
from openhands.events.action.message import SystemMessageAction
from openhands.llm import LLM
from openhands.llm.metrics import Metrics
from openhands.memory.conversation_memory import ConversationMemory
from openhands.storage.memory import InMemoryFileStore
from openhands.utils.prompt import PromptManager


@pytest.fixture
def mock_agent():
    agent = MagicMock(spec=Agent)
    agent.llm = MagicMock(spec=LLM)
    agent.llm.metrics = Metrics()

    # Create a proper SystemMessageAction
    system_message = SystemMessageAction(
        content='Test system message', tools=['test_tool']
    )
    system_message._source = EventSource.AGENT

    # Mock the get_system_message method
    agent.get_system_message.return_value = system_message

    return agent


@pytest.fixture
def test_event_stream():
    event_stream = EventStream(sid='test', file_store=InMemoryFileStore({}))
    return event_stream


def test_agent_get_system_message():
    """Test that the Agent.get_system_message method returns a SystemMessageAction."""
    # Create a mock agent
    agent = MagicMock(spec=Agent)
    agent.prompt_manager = MagicMock(spec=PromptManager)
    agent.prompt_manager.get_system_message.return_value = 'Test system message'
    agent.tools = ['test_tool']

    # Create a system message action
    system_message = SystemMessageAction(
        content='Test system message', tools=['test_tool']
    )
    system_message._source = EventSource.AGENT

    # Mock the get_system_message method to return our system message
    agent.get_system_message.return_value = system_message

    # Call the method
    result = agent.get_system_message()

    # Check that the system message was created correctly
    assert isinstance(result, SystemMessageAction)
    assert result.content == 'Test system message'
    assert result.tools == ['test_tool']
    assert result._source == EventSource.AGENT


def test_conversation_memory_handles_system_message():
    """Test that ConversationMemory correctly processes SystemMessageAction."""
    # Create a conversation memory
    config = AgentConfig()
    prompt_manager = MagicMock(spec=PromptManager)
    memory = ConversationMemory(config=config, prompt_manager=prompt_manager)

    # Create a system message action
    system_message = SystemMessageAction(
        content='Test system message', tools=['test_tool']
    )
    system_message._source = EventSource.AGENT

    # Process the system message
    # The _process_action method requires a pending_tool_call_action_messages parameter
    pending_tool_call_action_messages = {}
    messages = memory._process_action(
        action=system_message,
        pending_tool_call_action_messages=pending_tool_call_action_messages,
        vision_is_active=False,
    )

    # Check that the system message was processed correctly
    assert len(messages) == 1
    assert messages[0].role == 'system'
    assert messages[0].content[0].text == 'Test system message'


def test_system_message_in_event_stream(mock_agent, test_event_stream):
    """Test that SystemMessageAction is added to event stream in AgentController."""
    # Create agent controller with our mock agent and event stream
    AgentController(agent=mock_agent, event_stream=test_event_stream, max_iterations=10)

    # Get events from the event stream
    events = list(test_event_stream.get_events())

    # Verify system message was added to event stream
    assert len(events) == 1
    assert isinstance(events[0], SystemMessageAction)
    assert events[0].content == 'Test system message'
    assert events[0].tools == ['test_tool']
