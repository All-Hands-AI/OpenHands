import asyncio
import os

import pytest
from litellm.types.utils import ModelResponse

from openhands.agenthub.browsing_agent.browsing_agent import BrowsingAgent
from openhands.agenthub.codeact_agent.codeact_agent import CodeActAgent
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
from openhands.llm.metrics import Metrics
from openhands.storage.memory import InMemoryFileStore


class MockLLM(LLM):
    """Base class for mock LLMs used in testing."""

    def __init__(self, config: LLMConfig, completion_response: dict):
        super().__init__(config)
        self._completion_response = completion_response
        self._function_calling_active = True
        self.metrics = Metrics()

    def _completion(self, **kwargs) -> dict:
        return self._completion_response

    def vision_is_active(self) -> bool:
        return False

    def is_caching_prompt_active(self) -> bool:
        return False

    def format_messages_for_llm(self, messages: list) -> list:
        return messages

    def _post_completion(self, response: ModelResponse) -> float:
        return 0.0


@pytest.fixture
def mock_llm():
    """Creates a mock LLM for testing."""
    completion_response = {
        'choices': [
            {
                'message': {
                    'role': 'assistant',
                    'content': "I'll help with that task.",
                    'tool_calls': [
                        {
                            'id': 'call_1',
                            'type': 'function',
                            'function': {
                                'name': 'delegate',
                                'arguments': '{"agent": "BrowsingAgent", "inputs": {"task": "search for OpenHands repository"}}',
                            },
                        }
                    ],
                }
            }
        ]
    }
    return MockLLM(LLMConfig(), completion_response)


@pytest.fixture
def mock_browsing_llm():
    """Creates a mock LLM for the browsing agent."""
    completion_response = {
        'choices': [
            {
                'message': {
                    'role': 'assistant',
                    'content': "I've completed the search task.",
                    'tool_calls': [
                        {
                            'id': 'call_1',
                            'type': 'function',
                            'function': {
                                'name': 'finish',
                                'arguments': '{"message": "Found the repository at github.com/All-Hands-AI/OpenHands", "task_completed": "true"}',
                            },
                        }
                    ],
                }
            }
        ]
    }
    return MockLLM(LLMConfig(), completion_response)


@pytest.fixture
def mock_writer_llm():
    """Creates a mock LLM for the writer CodeAct agent."""
    completion_response = {
        'choices': [
            {
                'message': {
                    'role': 'assistant',
                    'content': "I'll help with that task.",
                    'tool_calls': [
                        {
                            'id': 'call_1',
                            'type': 'function',
                            'function': {
                                'name': 'delegate',
                                'arguments': '{"agent": "CodeActAgent", "inputs": {"task": "analyze the code in /workspace/example.py"}}',
                            },
                        }
                    ],
                }
            }
        ]
    }
    return MockLLM(LLMConfig(), completion_response)


@pytest.fixture
def mock_reader_llm():
    """Creates a mock LLM for the reader CodeAct agent."""
    completion_response = {
        'choices': [
            {
                'message': {
                    'role': 'assistant',
                    'content': "I've analyzed the code.",
                    'tool_calls': [
                        {
                            'id': 'call_1',
                            'type': 'function',
                            'function': {
                                'name': 'finish',
                                'arguments': '{"message": "The code has been analyzed. It contains a simple function.", "task_completed": "true"}',
                            },
                        }
                    ],
                }
            }
        ]
    }
    return MockLLM(LLMConfig(), completion_response)


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
    parent_config.codeact_enable_browsing = (
        True  # Enable browsing to allow delegation to BrowsingAgent
    )
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
    # Note: We don't need to store the child_controller since it's managed by the parent's delegate
    AgentController(
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
        content=[TextContent(text='Please search for the OpenHands repository')],
    )
    message_action = MessageAction(content=message.content[0].text)
    message_action._source = EventSource.USER

    # Process the message
    await parent_controller._on_event(message_action)
    await asyncio.sleep(0.5)  # Give time for processing

    # Verify delegation occurred
    events = list(event_stream.get_events())
    delegate_actions = [e for e in events if isinstance(e, AgentDelegateAction)]
    assert len(delegate_actions) == 1, 'Expected one delegation action'
    delegate_action = delegate_actions[0]
    assert delegate_action.agent == 'BrowsingAgent'
    assert 'search' in str(delegate_action.inputs)

    # Verify parent has a delegate controller
    assert parent_controller.delegate is not None
    assert parent_controller.delegate.agent.name == 'BrowsingAgent'

    # Let the child agent process its task
    child_message = Message(
        role='user', content=[TextContent(text=str(delegate_action.inputs))]
    )
    child_message_action = MessageAction(content=child_message.content[0].text)
    child_message_action._source = EventSource.USER
    await parent_controller.delegate._on_event(child_message_action)
    await asyncio.sleep(0.5)

    # Verify child completed its task
    events = list(event_stream.get_events())
    finish_actions = [e for e in events if isinstance(e, AgentFinishAction)]
    assert len(finish_actions) == 1, 'Expected one finish action'

    # Verify parent's delegate is cleared after child finishes
    assert parent_controller.delegate is None

    # Cleanup
    await parent_controller.close()


@pytest.mark.asyncio
async def test_codeact_to_codeact_delegation(mock_writer_llm, mock_reader_llm):
    """
    Test delegation between two CodeAct agents, where one is in read-only mode.
    This test verifies that:
    1. A CodeAct agent can delegate tasks to another CodeAct agent
    2. The reader CodeAct agent can operate in read-only mode
    3. The delegation flow works end-to-end with proper state management
    """
    # Setup event stream
    sid = 'test-codeact-delegation'
    file_store = InMemoryFileStore({})
    event_stream = EventStream(sid=sid, file_store=file_store)

    # Create example.py for testing
    os.makedirs('/workspace', exist_ok=True)
    with open('/workspace/example.py', 'w') as f:
        f.write('def hello():\n    print("Hello, World!")\n')

    # Create parent CodeAct agent with full capabilities
    parent_config = AgentConfig()
    parent_config.codeact_enable_jupyter = True
    parent_config.codeact_enable_llm_editor = True
    parent_config.codeact_enable_browsing = True  # Enable browsing to allow delegation
    parent_agent = CodeActAgent(mock_writer_llm, parent_config)
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

    # Create child CodeAct agent in read-only mode
    child_config = AgentConfig()
    child_config.codeact_enable_jupyter = True  # Enable Python execution
    child_config.codeact_enable_llm_editor = False  # Disable file editing
    child_agent = CodeActAgent(mock_reader_llm, child_config)
    child_state = State(max_iterations=10)
    # Note: We don't need to store the child_controller since it's managed by the parent's delegate
    AgentController(
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
        role='user', content=[TextContent(text='Please analyze the code in example.py')]
    )
    message_action = MessageAction(content=message.content[0].text)
    message_action._source = EventSource.USER

    # Process the message
    await parent_controller._on_event(message_action)
    await asyncio.sleep(0.5)  # Give time for processing

    # Verify delegation occurred
    events = list(event_stream.get_events())
    delegate_actions = [e for e in events if isinstance(e, AgentDelegateAction)]
    assert len(delegate_actions) == 1, 'Expected one delegation action'
    delegate_action = delegate_actions[0]
    assert delegate_action.agent == 'CodeActAgent'
    assert 'analyze' in str(delegate_action.inputs)

    # Verify parent has a delegate controller
    assert parent_controller.delegate is not None
    assert parent_controller.delegate.agent.name == 'CodeActAgent'

    # Let the child agent process its task
    child_message = Message(
        role='user', content=[TextContent(text=str(delegate_action.inputs))]
    )
    child_message_action = MessageAction(content=child_message.content[0].text)
    child_message_action._source = EventSource.USER
    await parent_controller.delegate._on_event(child_message_action)
    await asyncio.sleep(0.5)

    # Verify child completed its task
    events = list(event_stream.get_events())
    finish_actions = [e for e in events if isinstance(e, AgentFinishAction)]
    assert len(finish_actions) == 1, 'Expected one finish action'

    # Verify parent's delegate is cleared after child finishes
    assert parent_controller.delegate is None

    # Cleanup
    await parent_controller.close()
    os.remove('/workspace/example.py')
