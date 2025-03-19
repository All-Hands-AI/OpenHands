import asyncio
import os
import pytest
from typing import Any, Dict

from openhands.agenthub.codeact_agent.codeact_agent import CodeActAgent
from openhands.agenthub.browsing_agent.browsing_agent import BrowsingAgent
from openhands.controller.agent import Agent
from openhands.controller.agent_controller import AgentController
from openhands.controller.state.state import State
from openhands.core.config import AgentConfig, LLMConfig
from openhands.core.message import Message, TextContent
from openhands.events import EventSource, EventStream
from openhands.events.action import (
    AgentDelegateAction,
    AgentFinishAction,
    MessageAction,
)

from openhands.llm.llm import LLM
from openhands.storage.memory import InMemoryFileStore


@pytest.fixture
def mock_llm():
    """Creates a mock LLM for testing."""
    llm = LLM(LLMConfig())
    llm._completion = lambda **kwargs: {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": "I'll help with that task.",
                    "tool_calls": [
                        {
                            "id": "call_1",
                            "type": "function",
                            "function": {
                                "name": "delegate",
                                "arguments": '{"agent": "BrowsingAgent", "inputs": {"task": "search for OpenHands repository"}}'
                            }
                        }
                    ]
                }
            }
        ]
    }
    return llm


@pytest.fixture
def mock_browsing_llm():
    """Creates a mock LLM for the browsing agent."""
    llm = LLM(LLMConfig())
    llm._completion = lambda **kwargs: {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": "I've completed the search task.",
                    "tool_calls": [
                        {
                            "id": "call_1",
                            "type": "function",
                            "function": {
                                "name": "finish",
                                "arguments": '{"message": "Found the repository at github.com/All-Hands-AI/OpenHands", "task_completed": "true"}'
                            }
                        }
                    ]
                }
            }
        ]
    }
    return llm


@pytest.mark.asyncio
async def test_codeact_to_browsing_delegation(mock_llm, mock_browsing_llm):
    """
    Test delegation from CodeAct agent to BrowsingAgent.
    This test verifies that:
    1. CodeAct agent can delegate tasks to BrowsingAgent
    2. BrowsingAgent can receive and process the delegated task
    3. The delegation flow works end-to-end with proper state management
    """
    # Setup event stream
    sid = 'test-delegation'
    file_store = InMemoryFileStore({})
    event_stream = EventStream(sid=sid, file_store=file_store)

    # Create parent CodeAct agent
    parent_config = AgentConfig()
    parent_agent = CodeActAgent(mock_llm, parent_config)
    parent_state = State(max_iterations=10)
    parent_controller = AgentController(
        agent=parent_agent,
        event_stream=event_stream,
        max_iterations=10,
        sid='parent',
        confirmation_mode=False,
        headless_mode=True,
        initial_state=parent_state,
    )

    # Create child BrowsingAgent
    child_config = AgentConfig()
    child_agent = BrowsingAgent(mock_browsing_llm, child_config)
    child_state = State(max_iterations=10)
    child_controller = AgentController(
        agent=child_agent,
        event_stream=event_stream,
        max_iterations=10,
        sid='child',
        confirmation_mode=False,
        headless_mode=True,
        initial_state=child_state,
    )


    # Simulate a user message to trigger delegation
    message = Message(
        role='user',
        content=[TextContent(text='Please search for the OpenHands repository')]
    )
    message_action = MessageAction(content=message.content[0].text)
    message_action._source = EventSource.USER

    # Process the message
    await parent_controller._on_event(message_action)
    await asyncio.sleep(0.5)  # Give time for processing

    # Verify delegation occurred
    events = list(event_stream.get_events())
    delegate_actions = [e for e in events if isinstance(e, AgentDelegateAction)]
    assert len(delegate_actions) == 1, "Expected one delegation action"
    delegate_action = delegate_actions[0]
    assert delegate_action.agent == "BrowsingAgent"
    assert "search" in str(delegate_action.inputs)

    # Verify parent has a delegate controller
    assert parent_controller.delegate is not None
    assert parent_controller.delegate.agent.name == "BrowsingAgent"

    # Let the child agent process its task
    child_message = Message(
        role='user',
        content=[TextContent(text=str(delegate_action.inputs))]
    )
    child_message_action = MessageAction(content=child_message.content[0].text)
    child_message_action._source = EventSource.USER
    await parent_controller.delegate._on_event(child_message_action)
    await asyncio.sleep(0.5)

    # Verify child completed its task
    events = list(event_stream.get_events())
    finish_actions = [e for e in events if isinstance(e, AgentFinishAction)]
    assert len(finish_actions) == 1, "Expected one finish action"

    # Verify parent's delegate is cleared after child finishes
    assert parent_controller.delegate is None

    # Cleanup
    await parent_controller.close()
