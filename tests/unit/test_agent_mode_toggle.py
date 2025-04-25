import asyncio
from unittest.mock import MagicMock, Mock
from uuid import uuid4

import pytest

from openhands.agenthub.codeact_agent.codeact_agent import CodeActAgent
from openhands.agenthub.readonly_agent.readonly_agent import ReadOnlyAgent
from openhands.controller.agent import Agent
from openhands.controller.agent_controller import AgentController
from openhands.controller.state.state import State
from openhands.core.config import AgentConfig, LLMConfig
from openhands.core.schema import AgentState
from openhands.events import EventSource, EventStream
from openhands.events.action import (
    AgentDelegateAction,
    AgentFinishAction,
    MessageAction,
)
from openhands.events.observation import AgentDelegateObservation
from openhands.llm.llm import LLM
from openhands.llm.metrics import Metrics
from openhands.storage.memory import InMemoryFileStore


@pytest.fixture
def mock_event_stream():
    """Creates an event stream in memory."""
    sid = f'test-{uuid4()}'
    file_store = InMemoryFileStore({})
    return EventStream(sid=sid, file_store=file_store)


@pytest.fixture
def mock_codeact_agent():
    """Creates a mock CodeActAgent for testing."""
    agent = MagicMock(spec=CodeActAgent)
    agent.name = 'CodeActAgent'
    agent.llm = MagicMock(spec=LLM)
    agent.llm.metrics = Metrics()
    agent.llm.config = LLMConfig()
    agent.config = AgentConfig()

    # Add a proper system message mock
    from openhands.events.action.message import SystemMessageAction

    system_message = SystemMessageAction(content='Test system message for CodeActAgent')
    system_message._source = EventSource.AGENT
    system_message._id = -1  # Set invalid ID to avoid the ID check
    agent.get_system_message.return_value = system_message

    return agent


@pytest.fixture
def mock_readonly_agent():
    """Creates a mock ReadOnlyAgent for testing."""
    agent = MagicMock(spec=ReadOnlyAgent)
    agent.name = 'ReadOnlyAgent'
    agent.llm = MagicMock(spec=LLM)
    agent.llm.metrics = Metrics()
    agent.llm.config = LLMConfig()
    agent.config = AgentConfig()

    # Add a proper system message mock
    from openhands.events.action.message import SystemMessageAction

    system_message = SystemMessageAction(content='Test system message for ReadOnlyAgent')
    system_message._source = EventSource.AGENT
    system_message._id = -1  # Set invalid ID to avoid the ID check
    agent.get_system_message.return_value = system_message

    return agent


@pytest.mark.asyncio
async def test_agent_mode_toggle(mock_codeact_agent, mock_readonly_agent, mock_event_stream):
    """
    Test that the agent mode toggle works correctly:
    1. Start with CodeActAgent
    2. Toggle to ReadOnlyAgent
    3. Toggle back to CodeActAgent
    """
    # Mock the agent class resolution so that AgentController can instantiate mock_readonly_agent
    original_get_cls = Agent.get_cls
    
    def mock_get_cls(agent_name):
        if agent_name == 'ReadOnlyAgent':
            return lambda llm, config: mock_readonly_agent
        return original_get_cls(agent_name)
    
    Agent.get_cls = Mock(side_effect=mock_get_cls)

    # Create parent controller with CodeActAgent
    parent_state = State(max_iterations=10)
    parent_controller = AgentController(
        agent=mock_codeact_agent,
        event_stream=mock_event_stream,
        max_iterations=10,
        sid='parent',
        confirmation_mode=False,
        headless_mode=True,
        initial_state=parent_state,
    )

    # Verify we're starting with CodeActAgent
    assert parent_controller.agent.name == 'CodeActAgent'
    assert parent_controller.delegate is None

    # Create a delegate action to switch to ReadOnlyAgent
    delegate_action = AgentDelegateAction(
        agent='ReadOnlyAgent',
        inputs={
            'task': 'Continue the conversation in READ-ONLY MODE. You can explore and analyze code but cannot make changes.'
        },
        thought='Switching to read-only mode at user\'s request'
    )
    
    # Simulate the delegate action
    await parent_controller._on_event(delegate_action)
    
    # Give time for the async step() to execute
    await asyncio.sleep(0.5)
    
    # Verify that we've delegated to ReadOnlyAgent
    assert parent_controller.delegate is not None
    assert parent_controller.delegate.agent.name == 'ReadOnlyAgent'
    
    # Simulate a user message to the ReadOnlyAgent
    message_action = MessageAction(content='Show me the files in this directory')
    message_action._source = EventSource.USER
    await parent_controller.delegate._on_event(message_action)
    
    # Give time for the async step() to execute
    await asyncio.sleep(0.5)
    
    # Now simulate switching back to CodeActAgent with a finish action
    finish_action = AgentFinishAction(
        final_thought='Switching back to EXECUTE MODE. You now have full capabilities to modify code and execute commands.',
        task_completed=True,
        outputs={'mode_switch': True}
    )
    
    # Send the finish action to the delegate
    await parent_controller.delegate._on_event(finish_action)
    
    # Give time for the async step() to execute
    await asyncio.sleep(0.5)
    
    # Verify that we're back to the parent CodeActAgent
    assert parent_controller.delegate is None
    assert parent_controller.agent.name == 'CodeActAgent'
    
    # Verify that a delegate observation was added to the event stream
    events = list(mock_event_stream.get_events())
    assert any(isinstance(event, AgentDelegateObservation) for event in events)
    
    # Cleanup
    await parent_controller.close()
    
    # Restore the original get_cls method
    Agent.get_cls = original_get_cls