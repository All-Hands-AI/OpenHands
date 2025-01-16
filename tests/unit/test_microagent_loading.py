import json
import os
from unittest.mock import MagicMock

import pytest
from litellm import ModelResponse
from pytest import TempPathFactory

from openhands.agenthub.codeact_agent.codeact_agent import CodeActAgent
from openhands.controller.agent import Agent
from openhands.controller.state.state import State
from openhands.core.config import AgentConfig
from openhands.core.message import Message, TextContent
from openhands.events.action import MessageAction
from openhands.events.stream import EventStream
from openhands.microagent import BaseMicroAgent
from openhands.runtime.base import Runtime
from openhands.storage import get_file_store


@pytest.fixture
def temp_dir(tmp_path_factory: TempPathFactory) -> str:
    return str(tmp_path_factory.mktemp('test_microagent_loading'))


@pytest.fixture
def event_stream(temp_dir):
    file_store = get_file_store('local', temp_dir)
    event_stream = EventStream('asdf', file_store)
    yield event_stream


def test_microagent_loading(temp_dir):
    """Test that microagents are properly loaded from the runtime.
    
    The test verifies that:
    1. The agent loads microagents from the runtime
    2. The agent correctly matches triggers and enhances messages with microagent content
    """
    # Create a custom microagent file structure
    os.makedirs(os.path.join(temp_dir, '.openhands', 'microagents'))
    custom_agent_path = os.path.join(temp_dir, '.openhands', 'microagents', 'code_formatter.md')
    
    with open(custom_agent_path, 'w') as f:
        f.write("""---
name: code_formatter
type: knowledge
version: 1.0.0
agent: CoderAgent
triggers:
  - format code
  - code formatting
  - code style
---
# Code Formatter Agent
This agent helps format code according to style guidelines.

## Dependencies
- pip install black
- pip install isort

## Instructions
I help format code according to style guidelines. I can:
1. Format Python code using black
2. Sort imports using isort
3. Apply consistent code style across files
""")
    
    # Create a mock runtime that returns our microagent
    mock_runtime = MagicMock(spec=Runtime)
    mock_runtime.get_microagents_from_selected_repo.return_value = [
        BaseMicroAgent.load(custom_agent_path)
    ]
    
    # Create a mock state with the runtime
    mock_state = State(inputs={'runtime': mock_runtime})
    
    # Create a mock agent to test dependency extraction
    mock_llm = MagicMock()
    mock_llm.is_function_calling_active.return_value = True
    mock_response = ModelResponse(
        choices=[{
            'message': {
                'content': None,
                'tool_calls': [{
                    'id': 'call_1',
                    'function': {
                        'name': 'finish',
                        'arguments': '{}',
                    }
                }]
            }
        }]
    )
    mock_llm.completion.return_value = mock_response
    mock_llm.format_messages_for_llm.return_value = [
        {
            'role': 'user',
            'content': 'I need help with code formatting in this project',
        }
    ]
    
    # Create a message that should trigger the microagent
    message = Message(role='user', content=[TextContent(text='I need help with code formatting in this project')])
    
    # Create a CodeActAgent with use_microagents=True
    agent = Agent.get_cls('CodeActAgent')(
        llm=mock_llm,
        config=AgentConfig(memory_enabled=True, use_microagents=True)
    )
    
    # The agent should initialize its prompt_manager with microagents from the runtime
    agent.step(mock_state)
    
    # The message should be enhanced with the microagent's content
    agent.prompt_manager.enhance_message(message)
    
    # Verify that the microagent's content was added to the message
    assert len(message.content) == 2  # Original content + microagent content
    assert 'pip install black' in message.content[1].text