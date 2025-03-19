import pytest
from unittest.mock import MagicMock

from openhands.core.config.agent_config import AgentConfig
from openhands.core.message import Message, TextContent
from openhands.controller.state.state import State
from openhands.events.action.agent import AgentCondensationAction
from openhands.events.action.message import MessageAction
from openhands.memory.condenser.impl.llm_summarizing_condenser import LLMSummarizingCondenser
from openhands.memory.conversation_memory import ConversationMemory
from openhands.utils.prompt import PromptManager


@pytest.fixture
def agent_config():
    """Create a basic agent config for testing."""
    return AgentConfig(
        llm_config='test-model',
        enable_prompt_extensions=True,
    )


def test_agent_condensation_action_with_max_message_chars(agent_config):
    """Test that AgentCondensationAction respects max_message_chars parameter."""
    # Use a mock for the prompt manager
    prompt_manager = MagicMock(spec=PromptManager)
    prompt_manager.get_system_message.return_value = 'System message'
    memory = ConversationMemory(agent_config, prompt_manager)

    # Create some events to process
    event0 = MessageAction(content='Message 0')
    event0._id = 0  # ignore [attr-defined]
    
    # Create a mock condenser that will return our condensation action with a very long summary
    mock_condenser = MagicMock(spec=LLMSummarizingCondenser)
    
    # Create a long summary (15,000 characters)
    long_summary = "A" * 15000
    
    condensation_action = AgentCondensationAction(
        start_id=1,
        end_id=5,
        summary=long_summary,
    )

    # Set up the mock condenser to return our condensation action
    mock_condenser.condensed_history.return_value = [
        event0,  # Keep first event
        condensation_action,  # Condensation action with long summary
    ]

    # Create a state with our events
    state = State()
    state.history = [event0]

    # Process the events with a max_message_chars limit
    max_chars = 1000
    messages = memory.process_events(
        condensed_history=mock_condenser.condensed_history(state),
        initial_messages=[
            Message(role='system', content=[TextContent(text='System message')])
        ],
        max_message_chars=max_chars,
        vision_is_active=False,
    )

    # Verify that the condensation action was processed correctly and truncated
    assert len(messages) == 3  # system message + initial message + condensation action
    assert messages[0].role == 'system'
    assert messages[1].role == 'assistant'
    assert messages[2].role == 'user'
    
    # The content should be truncated
    condensed_content = messages[2].content[0].text
    assert len(condensed_content) < 15000
    assert '[... Observation truncated due to length ...]' in condensed_content
    
    # The truncated content should be approximately max_chars in length
    # (half from beginning, half from end, plus the truncation message)
    truncation_message = '\n[... Observation truncated due to length ...]\n'
    expected_length = (max_chars // 2) * 2 + len(truncation_message)
    assert abs(len(condensed_content) - expected_length) <= 1  # Allow for rounding


def test_agent_condensation_action_without_max_message_chars(agent_config):
    """Test that AgentCondensationAction doesn't truncate when max_message_chars is None."""
    # Use a mock for the prompt manager
    prompt_manager = MagicMock(spec=PromptManager)
    prompt_manager.get_system_message.return_value = 'System message'
    memory = ConversationMemory(agent_config, prompt_manager)

    # Create some events to process
    event0 = MessageAction(content='Message 0')
    event0._id = 0  # ignore [attr-defined]
    
    # Create a mock condenser that will return our condensation action
    mock_condenser = MagicMock(spec=LLMSummarizingCondenser)
    
    # Create a summary
    summary = "This is a condensed summary of the conversation"
    
    condensation_action = AgentCondensationAction(
        start_id=1,
        end_id=5,
        summary=summary,
    )

    # Set up the mock condenser to return our condensation action
    mock_condenser.condensed_history.return_value = [
        event0,  # Keep first event
        condensation_action,  # Condensation action
    ]

    # Create a state with our events
    state = State()
    state.history = [event0]

    # Process the events without a max_message_chars limit
    messages = memory.process_events(
        condensed_history=mock_condenser.condensed_history(state),
        initial_messages=[
            Message(role='system', content=[TextContent(text='System message')])
        ],
        max_message_chars=None,
        vision_is_active=False,
    )

    # Verify that the condensation action was processed correctly and not truncated
    assert len(messages) == 3  # system message + initial message + condensation action
    assert messages[0].role == 'system'
    assert messages[1].role == 'assistant'
    assert messages[2].role == 'user'
    
    # The content should not be truncated
    condensed_content = messages[2].content[0].text
    assert condensed_content == summary
    assert '[... Observation truncated due to length ...]' not in condensed_content