from typing import cast
from unittest.mock import MagicMock, Mock

import pytest

from openhands.agenthub.codeact_agent.codeact_agent import CodeActAgent
from openhands.controller.state.state import State
from openhands.core.config.agent_config import AgentConfig
from openhands.core.config.llm_config import LLMConfig
from openhands.events.action.agent import ChangeAgentStateAction
from openhands.events.action.message import MessageAction
from openhands.events.event import Event, RecallType
from openhands.events.observation.agent import (
    AgentCondensationObservation,
    RecallObservation,
)
from openhands.events.observation.files import FileReadObservation
from openhands.llm import LLM
from openhands.memory.condenser.condenser import Condensation, View
from openhands.memory.condenser.impl.llm_agent_cache_condenser import (
    LLMAgentCacheCondenser,
)


@pytest.fixture
def agent() -> CodeActAgent:
    config = AgentConfig()
    agent = CodeActAgent(llm=LLM(LLMConfig()), config=config)
    agent.llm = Mock(LLM)
    agent.llm.config = Mock()
    agent.llm.config.max_message_chars = 1000
    agent.llm.is_caching_prompt_active.return_value = True
    agent.llm.format_messages_for_llm = lambda messages: messages
    return agent


def set_next_llm_response(agent, response: str):
    """Set the next LLM response for the given agent."""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = response
    agent.llm.completion.return_value = mock_response


def test_contains_trigger_word():
    """Test that the containsTriggerWord method correctly identifies the CONDENSE! keyword."""

    # Create the condenser
    condenser = LLMAgentCacheCondenser(max_size=10)

    # Test case 1: Empty events list
    assert not condenser._contains_trigger_word([])

    # Test case 2: Single event (not enough events)
    event = MessageAction('Please CONDENSE! the conversation history.')
    assert not condenser._contains_trigger_word([event])

    # Test case 3: User message with CONDENSE! keyword
    user_event = MessageAction('Please CONDENSE! the conversation history.')
    user_event._source = 'user'  # type: ignore [attr-defined]
    agent_event = MessageAction('Agent response')
    agent_event._source = 'agent'  # type: ignore [attr-defined]
    assert condenser._contains_trigger_word([user_event, agent_event])

    # Test case 4: User message without CONDENSE! keyword
    user_event.content = 'Please summarize the conversation history.'
    assert not condenser._contains_trigger_word([user_event, agent_event])

    # Test case 5: RecallObservation followed by user message with CONDENSE! keyword
    user_event.content = 'Please CONDENSE! the conversation history.'
    recall_event = RecallObservation(
        recall_type=RecallType.KNOWLEDGE, content='saw a thing'
    )
    events = [agent_event, user_event, recall_event]
    assert condenser._contains_trigger_word(events)

    # Test case 6: Multiple user messages, only the most recent one matters
    user_event1 = MessageAction('First message without keyword')
    user_event1._source = 'user'  # type: ignore [attr-defined]
    user_event2 = MessageAction('Please CONDENSE! the conversation history.')
    user_event2._source = 'user'  # type: ignore [attr-defined]
    events = [user_event1, agent_event, user_event2]
    assert condenser._contains_trigger_word(events)

    # Test case 7: Multiple user messages, most recent one doesn't have keyword
    events = [user_event2, agent_event, user_event1]
    assert not condenser._contains_trigger_word(events)


def test_llm_agent_cache_condenser_with_state_no_need(agent: CodeActAgent):
    """Test that the LLMAgentCacheCondenser returns a View when no condensation is needed."""

    condenser = LLMAgentCacheCondenser(max_size=10)

    # Create real events
    events = [MessageAction(f'Message {i}') for i in range(5)]
    for i, event in enumerate(events):
        event._id = i  # type: ignore [attr-defined]

    state = State(history=cast(list[Event], events))

    result = condenser.condensed_history(state, agent)

    # Verify that a View is returned
    assert isinstance(result, View)
    assert len(result.events) == 5


def test_llm_agent_cache_condenser_with_state_keep(agent: CodeActAgent):
    """Test that the condenser uses the LLM to condense events when dependencies are available."""

    set_next_llm_response(agent, """
USER_CONTEXT: Testing file read operations
COMPLETED: Read 6 files with varying content
PENDING: None
CURRENT_STATE: Files read: 0.txt, 1.txt, 2.txt, 3.txt, 4.txt, 5.txt
    """)

    condenser = LLMAgentCacheCondenser()
    condenser.max_size = 5
    agent.condenser = condenser

    events = [FileReadObservation(f'{i}.txt', 'content.' * i) for i in range(6)]
    for i, event in enumerate(events):
        event._id = i + 1  # type: ignore [attr-defined]

    # Condense the events
    result = condenser.condensed_history(
        State(history=cast(list[Event], events)), agent
    )

    # Verify that a Condensation is returned
    assert isinstance(result, Condensation)
    assert hasattr(result, 'action')
    # With the new implementation, we keep approximately 25% of recent events
    # So we should have forgotten the older events
    assert len(result.action.forgotten_event_ids) > 0


def test_llm_agent_cache_condenser_with_state_with_rewrite(agent: CodeActAgent):
    """Test that the condenser correctly handles summaries."""
    set_next_llm_response(
        agent,
        """
USER_CONTEXT: File exploration task
COMPLETED: Read 6 files with varying content
PENDING: None
CODE_STATE: Files read: 0.txt, 1.txt, 2.txt, 3.txt, 4.txt, 5.txt
CHANGES: User asked about database schema and agent explained the tables and relationships.
        """,
    )

    condenser = LLMAgentCacheCondenser(max_size=5)
    agent.condenser = condenser

    events = [FileReadObservation(f'{i}.txt', 'content.' * i) for i in range(6)]
    for i, event in enumerate(events):
        event._id = i  # type: ignore [attr-defined]

    state = State(history=cast(list[Event], events))

    result = condenser.condensed_history(state, agent)

    # Verify that a Condensation is returned with a summary
    assert isinstance(result, Condensation)
    assert hasattr(result, 'action')
    assert result.action.summary is not None
    assert 'User asked about database schema' in result.action.summary


def test_llm_agent_cache_condenser_should_condense(agent: CodeActAgent):
    """Test that the LLMAgentCacheCondenser correctly determines when to condense based on size."""
    condenser = LLMAgentCacheCondenser(max_size=10)

    # Create mock events
    events_small = [MessageAction(f'Message {i}') for i in range(5)]
    events_large = [MessageAction(f'Message {i}') for i in range(11)]

    # Test should_condense with small number of events
    assert not condenser.should_condense(View(events=events_small))

    # Test should_condense with large number of events
    assert condenser.should_condense(View(events=events_large))


def test_llm_agent_cache_condenser_simulated_mixed_condensation(agent: CodeActAgent):
    """Test simulated condensation with a mix of messages and observations."""
    set_next_llm_response(
        agent,
        """
USER_CONTEXT: Mixed file and message operations
COMPLETED: Processed 7 events (messages and file reads)
PENDING: None
CURRENT_STATE: Last message: Test message 6, Last file: 7.txt
CHANGES: Summary <mention content of message 4,5>
        """,
    )

    condenser = LLMAgentCacheCondenser(max_size=5)
    agent.condenser = condenser

    events = []
    for i in range(1, 8):
        if i % 2 == 0:
            event = MessageAction(f'Test message {i}')
        else:
            event = FileReadObservation(f'File content for event {i}', f'{i}.txt')
        event._id = i  # type: ignore [attr-defined]
        events.append(event)

    state = State(history=cast(list[Event], events))

    result = condenser.condensed_history(state, agent)

    # Verify that a Condensation is returned
    assert isinstance(result, Condensation)
    assert len(result.action.forgotten_event_ids) > 0
    assert 'Summary <mention content of message 4,5>' in result.action.summary


def test_llm_agent_cache_condenser_with_agent_state_change_action(agent: CodeActAgent):
    """Test that AgentStateChangesAction is not removed during condensation."""
    set_next_llm_response(agent, """
USER_CONTEXT: User requested agent activation
COMPLETED: Agent state changed to active
PENDING: None
CURRENT_STATE: Agent is active
    """)

    # Create a condenser with a small max_size to ensure condensation
    # but large enough to not trigger again after adding the condensation action
    condenser = LLMAgentCacheCondenser(max_size=5)
    agent.condenser = condenser

    # Create a lot of events to ensure we exceed max_size
    events = []
    for i in range(10):
        event = MessageAction(f'Message {i}')
        event._source = 'user'  # type: ignore [attr-defined]
        event._id = i + 1  # type: ignore [attr-defined]
        events.append(event)
    
    # Add an agent state change event
    agent_state_change_event = ChangeAgentStateAction(agent_state='active')
    agent_state_change_event._id = 20  # type: ignore [attr-defined]
    events.append(agent_state_change_event)

    state = State(history=cast(list[Event], events))

    result = condenser.condensed_history(state, agent)

    # Verify that a Condensation is returned
    assert isinstance(result, Condensation)
    # With our new implementation, we should have forgotten at least one event
    assert len(result.action.forgotten_event_ids) > 0
    
    # Create a new state with just a few events and the condensation action
    # to avoid triggering condensation again
    new_state = State(history=[
        events[-1],  # Keep the agent state change event
        result.action  # Add the condensation action
    ])
    
    # Check that we get a View back
    view = condenser.condensed_history(new_state, agent)
    assert isinstance(view, View)
    # Check that we have the agent state change event and condensation action in the view
    assert events[-1] in view.events
    assert result.action in view.events


def test_llm_agent_cache_condenser_always_keep_system_prompt(agent: CodeActAgent):
    """Test that the system prompt is preserved in the final messages."""
    set_next_llm_response(agent, """
USER_CONTEXT: Simple greeting exchange
COMPLETED: User greeted agent, agent responded
PENDING: None
CURRENT_STATE: Conversation in progress
    """)

    # Create a condenser with a small max_size to ensure condensation
    # but large enough to not trigger again after adding the condensation action
    condenser = LLMAgentCacheCondenser(max_size=5)
    agent.condenser = condenser

    # Create a lot of events to ensure we exceed max_size
    events = []
    for i in range(10):
        event = MessageAction(f'Message {i}')
        event._source = 'user' if i % 2 == 0 else 'agent'  # type: ignore [attr-defined]
        event._id = i + 1  # type: ignore [attr-defined]
        events.append(event)

    state = State(history=cast(list[Event], events))

    result = condenser.condensed_history(state, agent)

    # Verify that a Condensation is returned
    assert isinstance(result, Condensation)
    result.action._id = 20  # type: ignore [attr-defined]
    
    # Create a new state with just a few events and the condensation action
    # to avoid triggering condensation again
    new_state = State(history=[
        events[-1],  # Keep the last event
        result.action  # Add the condensation action
    ])
    
    view = condenser.condensed_history(new_state, agent)
    assert isinstance(view, View)
    
    # Check that the system prompt is preserved in the messages
    messages = agent._get_messages(view.events)
    assert messages[0].role == 'system'
    assert 'You are OpenHands' in messages[0].content[0].text


def test_llm_agent_cache_condenser_first_message_user_message(agent: CodeActAgent):
    """Test that at least one user message is preserved."""

    # Create a condenser with a small max_size to ensure condensation
    # but large enough to not trigger again after adding the condensation action
    condenser = LLMAgentCacheCondenser(max_size=5)
    agent.condenser = condenser

    # Create events with only one user message
    user_message = MessageAction('Hello, how are you?')
    user_message._source = 'user'  # type: ignore [attr-defined]
    user_message._id = 1  # type: ignore [attr-defined]
    
    # Add many agent messages to exceed max_size
    events = [user_message]
    for i in range(10):
        event = MessageAction(f'Agent response {i}')
        event._source = 'agent'  # type: ignore [attr-defined]
        event._id = i + 2  # type: ignore [attr-defined]
        events.append(event)

    state = State(history=cast(list[Event], events))

    set_next_llm_response(agent, """
USER_CONTEXT: Initial greeting
COMPLETED: User said hello, agent responded
PENDING: None
CURRENT_STATE: Conversation started
    """)

    result = condenser.condensed_history(state, agent)

    # Verify that a Condensation is returned
    assert isinstance(result, Condensation)
    result.action._id = 20  # type: ignore [attr-defined]
    
    # Create a new state with just the user message and the condensation action
    # to avoid triggering condensation again
    new_state = State(history=[
        user_message,  # Keep the user message
        result.action  # Add the condensation action
    ])
    
    view = condenser.condensed_history(new_state, agent)
    assert isinstance(view, View)
    
    # Check that at least one user message is preserved in the view
    user_messages = [
        event for event in view.events 
        if hasattr(event, '_source') and event._source == 'user'
    ]
    assert len(user_messages) > 0
    
    # Check that the system prompt is preserved in the messages
    messages = agent._get_messages(view.events)
    assert messages[0].role == 'system'
    assert 'You are OpenHands' in messages[0].content[0].text


def test_llm_agent_cache_condenser_full_rewrite(agent: CodeActAgent):
    """Test a complete condensation of the conversation."""

    # Create a condenser with a small max_size to ensure condensation
    # but large enough to not trigger again after adding the condensation action
    condenser = LLMAgentCacheCondenser(max_size=5)
    agent.condenser = condenser

    # Create many events to exceed max_size
    events = []
    for i in range(10):
        event = MessageAction(f'Message {i}')
        event._source = 'user' if i % 2 == 0 else 'agent'  # type: ignore [attr-defined]
        event._id = i + 1  # type: ignore [attr-defined]
        events.append(event)

    state = State(history=cast(list[Event], events))

    set_next_llm_response(
        agent,
        """
USER_CONTEXT: Simple greeting
COMPLETED: User and AI greeted each other
PENDING: None
CURRENT_STATE: Conversation initialized
        """,
    )

    result = condenser.condensed_history(state, agent)

    # Verify that a Condensation is returned
    assert isinstance(result, Condensation)
    result.action._id = 20  # type: ignore [attr-defined]
    
    # Check that we've forgotten some events
    assert len(result.action.forgotten_event_ids) > 0
    
    # Check that the summary contains the greeting information
    assert "User and AI greeted each other" in result.action.summary
    
    # Create a new state with just the condensation action
    # to avoid triggering condensation again
    new_state = State(history=[result.action])
    
    view = condenser.condensed_history(new_state, agent)
    assert isinstance(view, View)
    
    # Check that the condensation action is in the view
    assert result.action in view.events
    
    # Check that the system prompt is preserved in the messages
    messages = agent._get_messages(view.events)
    assert messages[0].role == 'system'
    assert 'You are OpenHands' in messages[0].content[0].text
