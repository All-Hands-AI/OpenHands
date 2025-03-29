from unittest.mock import MagicMock, patch

import pytest

from openhands.controller.state.state import State
from openhands.core.message import Message
from openhands.events.event import Event
from openhands.llm import LLM
from openhands.memory.condenser.condenser import View, Condensation
from openhands.memory.condenser.impl.llm_agent_cache_condenser import (
    LLMAgentCacheCondenser,
)
from openhands.memory.conversation_memory import ConversationMemory
from openhands.utils.prompt import PromptManager


def test_contains_trigger_word():
    """Test that the containsTriggerWord method correctly identifies the CONDENSE! keyword."""
    # Mock the LLM
    mock_llm = MagicMock(spec=LLM)
    mock_llm.is_caching_prompt_active.return_value = True

    # Mock the agent
    mock_agent = MagicMock()
    mock_agent.llm = mock_llm

    # Create the condenser
    condenser = LLMAgentCacheCondenser(agent=mock_agent, max_size=10)

    # Test case 1: Empty events list
    assert condenser.containsTriggerWord([]) == False

    # Test case 2: Single event (not enough events)
    mock_event = MagicMock(spec=Event)
    assert condenser.containsTriggerWord([mock_event]) == False

    # Test case 3: User message with CONDENSE! keyword
    user_event = MagicMock(spec=Event)
    user_event.source = 'user'
    user_event.message = 'Please CONDENSE! the conversation history.'
    agent_event = MagicMock(spec=Event)
    agent_event.source = 'agent'
    assert condenser.containsTriggerWord([user_event, agent_event]) == True

    # Test case 4: User message without CONDENSE! keyword
    user_event.message = 'Please summarize the conversation history.'
    assert condenser.containsTriggerWord([user_event, agent_event]) == False

    # Test case 5: RecallObservation followed by user message with CONDENSE! keyword
    user_event.message = 'Please CONDENSE! the conversation history.'
    recall_event = MagicMock(spec=Event)
    recall_event.observation = 'recall'
    events = [agent_event, user_event, recall_event]
    assert condenser.containsTriggerWord(events) == True

    # Test case 6: Multiple user messages, only the most recent one matters
    user_event1 = MagicMock(spec=Event)
    user_event1.source = 'user'
    user_event1.message = 'First message without keyword'
    user_event2 = MagicMock(spec=Event)
    user_event2.source = 'user'
    user_event2.message = 'Please CONDENSE! the conversation history.'
    events = [user_event1, agent_event, user_event2]
    assert condenser.containsTriggerWord(events) == True

    # Test case 7: Multiple user messages, most recent one doesn't have keyword
    events = [user_event2, agent_event, user_event1]
    assert condenser.containsTriggerWord(events) == False


def test_llm_agent_cache_condenser_with_state_no_need():
    """Test that the LLMAgentCacheCondenser returns a View when no condensation is needed."""
    # Mock the LLM
    mock_llm = MagicMock(spec=LLM)
    mock_llm.is_caching_prompt_active.return_value = True

    # Mock the agent
    mock_agent = MagicMock()
    mock_agent.llm = mock_llm

    # Create the condenser with max_size=10
    condenser = LLMAgentCacheCondenser(agent=mock_agent, max_size=10)

    # Create mock events (less than max_size)
    mock_events = [MagicMock(spec=Event) for _ in range(5)]
    for i, event in enumerate(mock_events):
        event.id = i

    # Create a mock state with the events
    mock_state = MagicMock(spec=State)
    mock_state.history = mock_events

    # Condense the events
    result = condenser.condenseWithState(mock_state)

    # Verify that a View is returned
    assert isinstance(result, View)
    assert len(result.events) == 5


def test_llm_agent_cache_condenser_with_state_missing_dependencies():
    """Test that the condenser raises an exception when dependencies are missing."""
    # Mock the LLM with caching enabled for initialization
    mock_llm = MagicMock(spec=LLM)
    mock_llm.is_caching_prompt_active.return_value = True

    # Add config attribute to the mock LLM
    mock_llm_config = MagicMock()
    mock_llm_config.max_message_chars = 1000
    mock_llm.config = mock_llm_config
    mock_llm.vision_is_active.return_value = False

    # Create the agent with missing dependencies
    mock_agent = MagicMock()
    mock_agent.llm = mock_llm

    # Intentionally set conversation_memory to None to trigger the error
    mock_agent.conversation_memory = None
    mock_agent.prompt_manager = MagicMock(spec=PromptManager)

    # Create the condenser
    condenser = LLMAgentCacheCondenser(agent=mock_agent, max_size=5)

    # Create mock events (more than max_size)
    mock_events = [MagicMock(spec=Event) for _ in range(6)]
    for i, event in enumerate(mock_events):
        event.id = i

    # Create a mock state with the events
    mock_state = MagicMock(spec=State)
    mock_state.history = mock_events

    # Verify that an exception is raised due to missing conversation_memory
    with pytest.raises(ValueError, match="Missing conversation_memory or prompt_manager"):
        condenser.condenseWithState(mock_state)


@patch('openhands.memory.condenser.impl.llm_agent_cache_condenser.Message')
@patch('openhands.memory.condenser.impl.llm_agent_cache_condenser.TextContent')
def test_llm_agent_cache_condenser_with_state_with_dependencies(
    mock_text_content, mock_message
):
    """Test that the condenser uses the LLM to condense events when dependencies are available."""
    # Mock the LLM
    mock_llm = MagicMock(spec=LLM)
    mock_llm.is_caching_prompt_active.return_value = True
    mock_llm_config = MagicMock()
    mock_llm_config.max_message_chars = 1000
    mock_llm.config = mock_llm_config
    mock_llm.vision_is_active.return_value = False

    # Add metrics attribute to the mock LLM
    mock_metrics = MagicMock()
    mock_metrics.get.return_value = {"tokens": 100}
    mock_llm.metrics = mock_metrics

    # Mock the LLM response
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "KEEP: 0\nKEEP: 2\nKEEP: 4"
    mock_llm.completion.return_value = mock_response

    # Mock the conversation memory
    mock_conversation_memory = MagicMock(spec=ConversationMemory)
    mock_initial_messages = [MagicMock(spec=Message)]
    mock_conversation_memory.process_initial_messages.return_value = (
        mock_initial_messages
    )
    mock_processed_messages = [MagicMock(spec=Message) for _ in range(5)]
    mock_conversation_memory.process_events.return_value = mock_processed_messages

    # Mock the prompt manager
    mock_prompt_manager = MagicMock(spec=PromptManager)

    # Mock the agent
    mock_agent = MagicMock()
    mock_agent.llm = mock_llm
    mock_agent.conversation_memory = mock_conversation_memory
    mock_agent.prompt_manager = mock_prompt_manager

    # Create the condenser
    condenser = LLMAgentCacheCondenser(agent=mock_agent, max_size=5, keep_first=1)

    # Create mock events (more than max_size)
    mock_events = [MagicMock(spec=Event) for _ in range(6)]
    for i, event in enumerate(mock_events):
        event.id = i

    # Create a mock state with the events
    mock_state = MagicMock(spec=State)
    mock_state.history = mock_events

    # Condense the events
    result = condenser.condenseWithState(mock_state)

    # Verify that a Condensation is returned
    assert isinstance(result, Condensation)
    assert hasattr(result, 'action')
    assert result.action.forgotten == [1, 3, 5]


@patch('openhands.memory.condenser.impl.llm_agent_cache_condenser.Message')
@patch('openhands.memory.condenser.impl.llm_agent_cache_condenser.TextContent')
def test_llm_agent_cache_condenser_with_state_with_rewrite(
    mock_text_content, mock_message
):
    """Test that the condenser correctly handles REWRITE commands."""
    # Mock the LLM
    mock_llm = MagicMock(spec=LLM)
    mock_llm.is_caching_prompt_active.return_value = True
    mock_llm_config = MagicMock()
    mock_llm_config.max_message_chars = 1000
    mock_llm.config = mock_llm_config
    mock_llm.vision_is_active.return_value = False

    # Add metrics attribute to the mock LLM
    mock_metrics = MagicMock()
    mock_metrics.get.return_value = {"tokens": 100}
    mock_metrics.add = MagicMock()
    mock_llm.metrics = mock_metrics

    # Mock the LLM response with a REWRITE command
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message = MagicMock()
    mock_response.choices[
        0
    ].message.content = """
KEEP: 0
REWRITE 2 TO 4 WITH:
User asked about database schema and agent explained the tables and relationships.
END-REWRITE
KEEP: 5
"""
    mock_response.model_dump = MagicMock(return_value={})
    mock_llm.completion.return_value = mock_response
    mock_llm.format_messages_for_llm = lambda x: x

    # Mock the conversation memory
    mock_conversation_memory = MagicMock(spec=ConversationMemory)
    mock_initial_messages = [MagicMock(spec=Message)]
    mock_conversation_memory.process_initial_messages.return_value = (
        mock_initial_messages
    )
    mock_processed_messages = [MagicMock(spec=Message) for _ in range(5)]
    mock_conversation_memory.process_events.return_value = mock_processed_messages

    # Mock the prompt manager
    mock_prompt_manager = MagicMock(spec=PromptManager)

    # Create a mock agent with the required components
    mock_agent = MagicMock()
    mock_agent.llm = mock_llm
    mock_agent.conversation_memory = mock_conversation_memory
    mock_agent.prompt_manager = mock_prompt_manager

    # Create the condenser with max_size=5 to force condensation
    condenser = LLMAgentCacheCondenser(
        agent=mock_agent,
        max_size=5,  # Set to 5 to force condensation since we have 6 events
        keep_first=1,
    )

    # Create mock events with IDs
    mock_events = []
    for i in range(6):
        event = MagicMock(spec=Event)
        event.id = i
        mock_events.append(event)

    # Create a mock state with the events
    mock_state = MagicMock(spec=State)
    mock_state.history = mock_events

    # Force the should_condense method to return True
    with patch.object(condenser, 'should_condense', return_value=True):
        # Condense the events
        result = condenser.condenseWithState(mock_state)

    # Verify that a Condensation is returned with a summary
    assert isinstance(result, Condensation)
    assert hasattr(result, 'action')
    assert result.action.summary is not None
    assert "User asked about database schema" in result.action.summary