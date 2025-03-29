from unittest.mock import MagicMock, patch

import pytest

from openhands.core.message import Message
from openhands.events.event import Event
from openhands.llm import LLM
from openhands.memory.condenser.condenser import View, Condensation
from openhands.memory.condenser.impl.llm_agent_cache_condenser import (
    LLMAgentCacheCondenser,
)
from openhands.memory.conversation_memory import ConversationMemory
from openhands.utils.prompt import PromptManager


def test_llm_agent_cache_condenser_init():
    """Test that the LLMAgentCacheCondenser initializes correctly."""
    # Mock the LLM
    mock_llm = MagicMock(spec=LLM)
    mock_llm.is_caching_prompt_active.return_value = True

    # Mock the conversation memory and prompt manager
    mock_conversation_memory = MagicMock(spec=ConversationMemory)
    mock_prompt_manager = MagicMock(spec=PromptManager)

    # Mock the agent
    mock_agent = MagicMock()
    mock_agent.llm = mock_llm
    mock_agent.conversation_memory = mock_conversation_memory
    mock_agent.prompt_manager = mock_prompt_manager

    # Create the condenser
    condenser = LLMAgentCacheCondenser(agent=mock_agent, max_size=100, keep_first=1)

    # Verify that the condenser has the correct attributes
    assert condenser.agent is mock_agent
    assert condenser.llm is mock_llm
    assert condenser.conversation_memory is mock_conversation_memory
    assert condenser.prompt_manager is mock_prompt_manager
    assert condenser.max_size == 100
    assert condenser.keep_first == 1


def test_llm_agent_cache_condenser_init_caching_disabled():
    """Test that the LLMAgentCacheCondenser raises an exception when caching is disabled."""
    # Mock the LLM with caching disabled
    mock_llm = MagicMock(spec=LLM)
    mock_llm.is_caching_prompt_active.return_value = False

    # Mock the conversation memory and prompt manager
    mock_conversation_memory = MagicMock(spec=ConversationMemory)
    mock_prompt_manager = MagicMock(spec=PromptManager)

    # Mock the agent
    mock_agent = MagicMock()
    mock_agent.llm = mock_llm
    mock_agent.conversation_memory = mock_conversation_memory
    mock_agent.prompt_manager = mock_prompt_manager

    # Verify that creating the condenser raises an exception
    with pytest.raises(ValueError, match="LLM does not support prompt caching"):
        LLMAgentCacheCondenser(agent=mock_agent)


def test_llm_agent_cache_condenser_should_condense():
    """Test that the LLMAgentCacheCondenser correctly determines when to condense based on size."""
    # Mock the LLM
    mock_llm = MagicMock(spec=LLM)
    mock_llm.is_caching_prompt_active.return_value = True

    # Mock the agent
    mock_agent = MagicMock()
    mock_agent.llm = mock_llm

    # Create the condenser with max_size=5
    condenser = LLMAgentCacheCondenser(agent=mock_agent, max_size=5)

    # Create mock events
    mock_events_small = [MagicMock(spec=Event) for _ in range(5)]
    mock_events_large = [MagicMock(spec=Event) for _ in range(6)]

    # Test should_condense with small number of events
    assert not condenser.should_condense(mock_events_small)

    # Test should_condense with large number of events
    assert condenser.should_condense(mock_events_large)


def test_llm_agent_cache_condenser_should_condense_with_condense_keyword():
    """Test that the LLMAgentCacheCondenser condenses when the last message contains CONDENSE!."""
    # Mock the LLM
    mock_llm = MagicMock(spec=LLM)
    mock_llm.is_caching_prompt_active.return_value = True

    # Mock the agent
    mock_agent = MagicMock()
    mock_agent.llm = mock_llm

    # Create the condenser with max_size=10 (large enough to not trigger size-based condensation)
    condenser = LLMAgentCacheCondenser(agent=mock_agent, max_size=10)

    # Create mock events with the last one being a user message containing "CONDENSE!"
    mock_events = [MagicMock(spec=Event) for _ in range(3)]

    # The last event should be a user message with "CONDENSE!" in the message
    mock_user_message = MagicMock(spec=Event)
    mock_user_message.source = 'user'
    mock_user_message.message = "Please CONDENSE! the conversation history."
    mock_events.append(mock_user_message)

    # Verify that the condenser detects the CONDENSE! keyword
    assert condenser.should_condense(mock_events)

    # Create mock events without the CONDENSE! keyword
    mock_events_no_keyword = [MagicMock(spec=Event) for _ in range(3)]
    mock_user_message_no_keyword = MagicMock(spec=Event)
    mock_user_message_no_keyword.source = 'user'
    mock_user_message_no_keyword.message = "Please continue."
    mock_events_no_keyword.append(mock_user_message_no_keyword)

    # Verify that the condenser doesn't condense without the keyword
    assert not condenser.should_condense(mock_events_no_keyword)


def test_llm_agent_cache_condenser_condense_no_need():
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

    # Condense the events
    result = condenser.condense(mock_events)

    # Verify that a View is returned
    assert isinstance(result, View)
    assert len(result.events) == 5


def test_llm_agent_cache_condenser_condense_missing_dependencies():
    """Test that the condenser raises an exception when dependencies are missing."""
    # Mock the LLM
    mock_llm = MagicMock(spec=LLM)
    mock_llm.is_caching_prompt_active.return_value = True

    # Mock the agent with missing dependencies
    mock_agent = MagicMock()
    mock_agent.llm = mock_llm
    mock_agent.conversation_memory = None
    mock_agent.prompt_manager = None

    # Create the condenser with max_size=5 but no conversation_memory or prompt_manager
    condenser = LLMAgentCacheCondenser(agent=mock_agent, max_size=5)

    # Create mock events (more than max_size)
    mock_events = [MagicMock(spec=Event) for _ in range(6)]

    # Verify that condensing the events raises an exception
    with pytest.raises(
        ValueError, match="Missing conversation_memory or prompt_manager"
    ):
        condenser.condense(mock_events)


@patch('openhands.memory.condenser.impl.llm_agent_cache_condenser.Message')
@patch('openhands.memory.condenser.impl.llm_agent_cache_condenser.TextContent')
def test_llm_agent_cache_condenser_condense_with_dependencies(
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

    # Condense the events
    result = condenser.condense(mock_events)

    # Verify that the conversation memory methods were called
    mock_conversation_memory.process_initial_messages.assert_called_once_with(
        with_caching=True
    )
    mock_conversation_memory.process_events.assert_called_once()

    # Verify that the LLM was called
    mock_llm.completion.assert_called_once()

    # Verify that a Condensation is returned
    assert isinstance(result, Condensation)

    # Verify that the correct event IDs are forgotten (all except 0, 2, 4)
    # Event 0 is kept because it's in the keep_first range
    # Events 2 and 4 are kept because they're in the LLM response
    # Events 1, 3, and 5 should be forgotten
    assert set(result.action.forgotten_event_ids) == {1, 3, 5}


@patch('openhands.memory.condenser.impl.llm_agent_cache_condenser.Message')
@patch('openhands.memory.condenser.impl.llm_agent_cache_condenser.TextContent')
def test_llm_agent_cache_condenser_condense_with_rewrite(
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

    # Force the should_condense method to return True
    with patch.object(condenser, 'should_condense', return_value=True):
        # Condense the events
        result = condenser.condense(mock_events)

    # Verify that a Condensation is returned
    assert isinstance(result, Condensation)

    # Verify that the correct event IDs are forgotten
    # Event 0 is kept because it's in the keep_first range
    # Events 2, 3, 4 should be forgotten because they're in the REWRITE range
    # Event 5 is kept because it's in the KEEP list
    # Event 1 should be forgotten because it's not in any KEEP list
    assert set(result.action.forgotten_event_ids) == {1, 2, 3, 4}

    # Verify that the summary contains the REWRITE content
    expected_content = "User asked about database schema and agent explained the tables and relationships."
    assert expected_content in result.action.summary
