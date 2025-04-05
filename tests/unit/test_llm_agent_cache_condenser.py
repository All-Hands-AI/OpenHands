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
from openhands.events.observation.agent import RecallObservation
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

    set_next_llm_response(agent, 'KEEP: 0\nKEEP: 1\nKEEP: 3\nKEEP: 5')

    condenser = LLMAgentCacheCondenser()
    condenser.max_size = 5
    agent.condenser = condenser

    events = [FileReadObservation(f'{i}.txt', 'content.' * i) for i in range(6)]
    for i, event in enumerate(events):
        # Assigning IDs starting from 1, so that they match the index of the messages
        # that the LLM is told to use.
        event._id = i + 1  # type: ignore [attr-defined]

    # Condense the events
    result = condenser.condensed_history(
        State(history=cast(list[Event], events)), agent
    )

    # Verify that a Condensation is returned
    assert isinstance(result, Condensation)
    assert hasattr(result, 'action')
    assert result.action.forgotten_event_ids == [2, 4, 6]


def test_llm_agent_cache_condenser_with_state_with_rewrite(agent: CodeActAgent):
    """Test that the condenser correctly handles REWRITE commands."""
    set_next_llm_response(
        agent,
        """
        KEEP: 0
        KEEP: 1
        REWRITE 2 TO 4 WITH:
        User asked about database schema and agent explained the tables and relationships.
        END-REWRITE
        KEEP: 5
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
        KEEP: 0
        KEEP: 1
        KEEP: 2
        REWRITE 4 TO 5 WITH:
        Summary <mention content of message 4,5>
        END-REWRITE
        KEEP: 6
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
    assert result.action.forgotten_event_ids == [3, 4, 5, 7]
    assert 'Summary <mention content of message 4,5>' in result.action.summary


def test_llm_agent_cache_condenser_with_agent_state_change_action(agent: CodeActAgent):
    """Test that AgentStateChangesAction is not removed during condensation."""
    set_next_llm_response(agent, 'KEEP: 0\nKEEP: 1')

    condenser = LLMAgentCacheCondenser()
    agent.condenser = condenser

    first_message_event = MessageAction('first message')
    first_message_event._source = 'user'  # type: ignore [attr-defined]
    first_message_event._id = 1  # type: ignore [attr-defined]
    agent_state_change_event = ChangeAgentStateAction(agent_state='active')
    agent_state_change_event._id = 2  # type: ignore [attr-defined]
    message_action_condense = MessageAction('CONDENSE!')
    message_action_condense._source = 'user'  # type: ignore [attr-defined]
    message_action_condense._id = 3  # type: ignore [attr-defined]

    state = State(
        history=[first_message_event, agent_state_change_event, message_action_condense]
    )

    result = condenser.condensed_history(state, agent)

    # Verify that a Condensation is returned
    assert isinstance(result, Condensation)
    assert result.action.forgotten_event_ids == [message_action_condense.id]

    # Apply the condensation
    result.action._id = 4  # type: ignore [attr-defined]
    state.history.append(result.action)
    view = condenser.condensed_history(state, agent)
    assert isinstance(view, View)
    assert view.events == [
        first_message_event,
        agent_state_change_event,
        result.action,
    ]


def test_llm_agent_cache_condenser_always_keep_system_prompt(agent: CodeActAgent):
    """Test that the system prompt is not removed if the agent does not send KEEP 0."""
    set_next_llm_response(agent, 'KEEP: 1\nKEEP: 2')

    condenser = LLMAgentCacheCondenser()
    agent.condenser = condenser

    first_message = MessageAction('Hello, how are you?')
    first_message._source = 'user'  # type: ignore [attr-defined]
    first_message._id = 1  # type: ignore [attr-defined]
    assistant_message_event = MessageAction('Great!')
    assistant_message_event._source = 'agent'  # type: ignore [attr-defined]
    assistant_message_event._id = 2  # type: ignore [attr-defined]
    user_condensation_message_event = MessageAction('NOW CONDENSE!')
    user_condensation_message_event._source = 'user'  # type: ignore [attr-defined]
    user_condensation_message_event._id = 3  # type: ignore [attr-defined]

    state = State(
        history=[
            first_message,
            assistant_message_event,
            user_condensation_message_event,
        ]
    )

    result = condenser.condensed_history(state, agent)

    # Verify that a Condensation is returned
    assert isinstance(result, Condensation)
    result.action._id = 7  # type: ignore [attr-defined]
    state.history.append(result.action)
    assert result.action.forgotten_event_ids == [3]

    view = condenser.condensed_history(state, agent)
    assert isinstance(view, View)
    assert view.events == [first_message, assistant_message_event, result.action]

    messages = agent._get_messages(view.events)
    assert messages[0].role == 'system'
    assert 'You are OpenHands' in messages[0].content[0].text
    assert len(messages) == 3


def test_llm_agent_cache_condenser_first_message_user_message(agent: CodeActAgent):
    """Do not allow the LLM to remove all conversation messages."""

    condenser = LLMAgentCacheCondenser()
    agent.condenser = condenser

    first_message = MessageAction('Hello, how are you?')
    first_message._source = 'user'  # type: ignore [attr-defined]
    first_message._id = 1  # type: ignore [attr-defined]
    assistant_message_event = MessageAction('Great!')
    assistant_message_event._source = 'agent'  # type: ignore [attr-defined]
    assistant_message_event._id = 2  # type: ignore [attr-defined]
    user_condensation_message_event = MessageAction('NOW CONDENSE!')
    user_condensation_message_event._source = 'user'  # type: ignore [attr-defined]
    user_condensation_message_event._id = 3  # type: ignore [attr-defined]

    state = State(
        history=[
            first_message,
            assistant_message_event,
            user_condensation_message_event,
        ]
    )

    set_next_llm_response(agent, 'KEEP: 0')

    result = condenser.condensed_history(state, agent)

    # Verify that a Condensation is returned
    assert isinstance(result, Condensation)
    result.action._id = 7  # type: ignore [attr-defined]
    state.history.append(result.action)
    assert result.action.forgotten_event_ids == [2, 3]

    view = condenser.condensed_history(state, agent)
    assert isinstance(view, View)
    assert view.events == [first_message, result.action]

    messages = agent._get_messages(view.events)
    assert messages[0].role == 'system'
    assert 'You are OpenHands' in messages[0].content[0].text
    assert len(messages) == 2
