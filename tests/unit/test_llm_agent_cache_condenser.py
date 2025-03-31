from unittest.mock import MagicMock

from openhands.agenthub.llm_cache_code_agent.llm_cache_code_agent import (
    LLMCacheCodeAgent,
)
from openhands.controller.state.state import State
from openhands.core.config.agent_config import AgentConfig
from openhands.events.action.message import MessageAction
from openhands.events.event import Event, RecallType
from openhands.events.observation.agent import RecallObservation
from openhands.events.observation.files import FileReadObservation
from openhands.llm import LLM
from openhands.memory.condenser.condenser import Condensation, View
from openhands.memory.condenser.impl.llm_agent_cache_condenser import (
    LLMAgentCacheCondenser,
)


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
    assert not condenser.containsTriggerWord([])

    # Test case 2: Single event (not enough events)
    event = MessageAction('Please CONDENSE! the conversation history.')
    assert not condenser.containsTriggerWord([event])

    # Test case 3: User message with CONDENSE! keyword
    user_event = MessageAction('Please CONDENSE! the conversation history.')
    user_event._source = 'user'
    agent_event = MessageAction('Agent response')
    agent_event._source = 'agent'
    assert condenser.containsTriggerWord([user_event, agent_event])

    # Test case 4: User message without CONDENSE! keyword
    user_event.content = 'Please summarize the conversation history.'
    assert not condenser.containsTriggerWord([user_event, agent_event])

    # Test case 5: RecallObservation followed by user message with CONDENSE! keyword
    user_event.content = 'Please CONDENSE! the conversation history.'
    recall_event = RecallObservation(
        recall_type=RecallType.KNOWLEDGE, content='saw a thing'
    )
    events = [agent_event, user_event, recall_event]
    assert condenser.containsTriggerWord(events)

    # Test case 6: Multiple user messages, only the most recent one matters
    user_event1 = MessageAction('First message without keyword')
    user_event1._source = 'user'
    user_event2 = MessageAction('Please CONDENSE! the conversation history.')
    user_event2._source = 'user'
    events = [user_event1, agent_event, user_event2]
    assert condenser.containsTriggerWord(events)

    # Test case 7: Multiple user messages, most recent one doesn't have keyword
    events = [user_event2, agent_event, user_event1]
    assert not condenser.containsTriggerWord(events)


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


def test_llm_agent_cache_condenser_with_state_keep():
    """Test that the condenser uses the LLM to condense events when dependencies are available."""
    # Create a real LLM instance with caching enabled
    mock_llm = MagicMock(spec=LLM)
    mock_llm.is_caching_prompt_active.return_value = True
    mock_llm_config = MagicMock()
    mock_llm_config.max_message_chars = 1000
    mock_llm.config = mock_llm_config
    mock_llm.vision_is_active.return_value = False

    # Add metrics attribute to the LLM
    mock_metrics = MagicMock()
    mock_metrics.get.return_value = {'tokens': 100}
    mock_llm.metrics = mock_metrics

    # Mock the LLM response
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = 'KEEP: 0\nKEEP: 1\nKEEP: 3\nKEEP: 5'
    mock_llm.completion.return_value = mock_response

    agentConfig = AgentConfig()
    agent = LLMCacheCodeAgent(mock_llm, agentConfig)

    condenser = agent.condenser
    condenser.max_size = 5

    events = [FileReadObservation(f'{i}.txt', 'content.' * i) for i in range(6)]
    for i, event in enumerate(events):
        # Assigning IDs starting from 1, so that they match the index of the messages
        # that the LLM is told to use.
        event._id = i + 1

    # Create a mock state with the events
    mock_state = MagicMock(spec=State)
    mock_state.history = events

    # Condense the events
    result = condenser.condenseWithState(mock_state)

    # Verify that a Condensation is returned
    assert isinstance(result, Condensation)
    assert hasattr(result, 'action')
    assert result.action.forgotten_event_ids == [2, 4, 6]


def test_llm_agent_cache_condenser_with_state_with_rewrite():
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
    mock_metrics.get.return_value = {'tokens': 100}
    mock_metrics.add = MagicMock()
    mock_llm.metrics = mock_metrics

    # Mock the LLM response with a REWRITE command
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message = MagicMock()
    mock_response.choices[0].message.content = """
KEEP: 0
KEEP: 1
REWRITE 2 TO 4 WITH:
User asked about database schema and agent explained the tables and relationships.
END-REWRITE
KEEP: 5
"""
    mock_response.model_dump = MagicMock(return_value={})
    mock_llm.completion.return_value = mock_response
    mock_llm.format_messages_for_llm = lambda x: x

    agentConfig = AgentConfig()
    agent = LLMCacheCodeAgent(mock_llm, agentConfig)

    condenser = agent.condenser
    condenser.max_size = 5

    events = [FileReadObservation(f'{i}.txt', 'content.' * i) for i in range(6)]
    for i, event in enumerate(events):
        event._id = i

    # Create a mock state with the events
    mock_state = MagicMock(spec=State)
    mock_state.history = events

    result = condenser.condenseWithState(mock_state)

    # Verify that a Condensation is returned with a summary
    assert isinstance(result, Condensation)
    assert hasattr(result, 'action')
    assert result.action.summary is not None
    assert 'User asked about database schema' in result.action.summary


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
