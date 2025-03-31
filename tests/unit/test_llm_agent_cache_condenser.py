from unittest.mock import MagicMock

from openhands.agenthub.llm_cache_code_agent.llm_cache_code_agent import (
    LLMCacheCodeAgent,
)
from openhands.controller.state.state import State
from openhands.core.config.agent_config import AgentConfig
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


def test_llm_agent_cache_condenser_simulated_mixed_condensation():
    """Test simulated condensation with a mix of messages and observations."""
    # Create a mock LLM with caching enabled
    mock_llm = MagicMock(spec=LLM)
    mock_llm.is_caching_prompt_active.return_value = True
    mock_llm.config = MagicMock(max_message_chars=1000)
    mock_llm.vision_is_active.return_value = False
    mock_llm.metrics = MagicMock()
    mock_llm.metrics.get.return_value = {'tokens': 100}

    # Create an agent instance with the mock LLM
    agent_config = AgentConfig()
    agent = LLMCacheCodeAgent(mock_llm, agent_config)

    # Configure the condenser
    condenser = agent.condenser
    condenser.max_size = 5

    # Create a mix of events: alternating between MessageAction and FileReadObservation
    events = []
    for i in range(1, 8):
        if i % 2 == 0:
            event = MessageAction(f'Test message {i}')
        else:
            event = FileReadObservation(f'File content for event {i}', f'{i}.txt')
        event._id = i  # Use _id instead of id
        events.append(event)

    mock_state = MagicMock(spec=State)
    mock_state.history = events

    # Simulate the LLM response for condensation
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = (
        'KEEP: 0\n'
        'KEEP: 1\n'
        'KEEP: 2\n'
        'REWRITE 4 TO 5 WITH:\n'
        'Summary <mention content of message 4,5>\n'
        'END-REWRITE\n'
        'KEEP: 6'
    )
    mock_llm.completion.return_value = mock_response

    result = condenser.condenseWithState(mock_state)
    assert isinstance(result, Condensation)

    assert result.action.forgotten_event_ids == [3, 4, 5, 7]
    assert 'Summary <mention content of message 4,5>' in result.action.summary


def test_llm_agent_cache_condenser_with_agent_state_change_action():
    """Test that AgentStateChangesAction is not removed during condensation."""
    # Mock the LLM
    mock_llm = MagicMock(spec=LLM)
    mock_llm.is_caching_prompt_active.return_value = True
    mock_llm.config = MagicMock(max_message_chars=1000)
    mock_llm.vision_is_active.return_value = False
    mock_llm.metrics = MagicMock()
    mock_llm.metrics.get.return_value = {'tokens': 100}

    # Create an agent instance with the mock LLM
    agent_config = AgentConfig()
    agent = LLMCacheCodeAgent(mock_llm, agent_config)

    condenser = agent.condenser

    first_message_event = MessageAction('first message')
    first_message_event._source = 'user'
    first_message_event._id = 1
    # this event is not sent to the llm at all. So it should be kept
    # and not forgotten
    agent_state_change_event = ChangeAgentStateAction(agent_state='active')
    agent_state_change_event._id = 2
    message_action_condense = MessageAction('CONDENSE!')
    message_action_condense._source = 'user'
    message_action_condense._id = 3

    state = State(
        history=[first_message_event, agent_state_change_event, message_action_condense]
    )

    # Simulate the LLM response for condensation
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = 'KEEP: 0\nKEEP: 1'
    mock_llm.completion.return_value = mock_response

    condensation = condenser.condenseWithState(state)

    assert isinstance(condensation, Condensation)
    assert condensation.action.forgotten_event_ids == [message_action_condense.id]

    # Apply the condensation
    condensation.action._id = 4
    state.history.append(condensation.action)
    view = condenser.condenseWithState(state)
    assert isinstance(view, View)
    assert view.events == [
        first_message_event,
        agent_state_change_event,
        condensation.action,
    ]

    # Continue after condensation
    msg_afer_condensation = MessageAction('First message after second condensation')
    msg_afer_condensation._id = 5
    state.history.append(msg_afer_condensation)
    view = condenser.condenseWithState(state)
    assert isinstance(view, View)
    assert view.events == [
        first_message_event,
        agent_state_change_event,
        condensation.action,
        msg_afer_condensation,
    ]

    # Do a second condensation
    message_action_condense2 = MessageAction(
        'Remember this important info. Then CONDENSE!'
    )
    message_action_condense2._source = 'user'
    message_action_condense2._id = 6
    state.history.append(message_action_condense2)

    # Simulate the LLM response for condensation
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = 'KEEP: 0\nKEEP: 3'
    mock_llm.completion.return_value = mock_response

    condensation2 = condenser.condenseWithState(state)

    # Verify that a Condensation is returned and both events are kept
    assert isinstance(condensation2, Condensation)
    assert condensation2.action.forgotten_event_ids == [
        first_message_event.id,
        msg_afer_condensation.id,
    ]

    # Apply the condensation
    condensation2.action._id = 7
    state.history.append(condensation2.action)
    view = condenser.condenseWithState(state)
    assert isinstance(view, View)
    assert view.events == [
        agent_state_change_event,
        condensation.action,
        message_action_condense2,
        condensation2.action,
    ]


def test_llm_agent_cache_condenser_always_keep_system_prompt():
    """Test that the system prompt is not removed if the agent does not send KEEP 0."""

    mock_llm = MagicMock(spec=LLM)
    mock_llm.is_caching_prompt_active.return_value = True
    mock_llm.config = MagicMock(max_message_chars=1000)
    mock_llm.vision_is_active.return_value = False
    mock_llm.metrics = MagicMock()
    mock_llm.metrics.get.return_value = {'tokens': 100}

    agent_config = AgentConfig()
    agent = LLMCacheCodeAgent(mock_llm, agent_config)

    condenser = agent.condenser

    first_message = MessageAction('Hello, how are you?')
    first_message._source = 'user'
    first_message._id = 1
    assistant_message_event = MessageAction('Great!')
    assistant_message_event._source = 'agent'
    assistant_message_event._id = 2
    user_condensation_message_event = MessageAction('NOW CONDENSE!')
    user_condensation_message_event._source = 'user'
    user_condensation_message_event._id = 3

    state = State(
        history=[
            first_message,
            assistant_message_event,
            user_condensation_message_event,
        ]
    )

    # Simulate the LLM response for condensation
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = 'KEEP: 1\nKEEP: 2'
    mock_llm.completion.return_value = mock_response

    # Perform condensation
    condensation = condenser.condenseWithState(state)

    assert isinstance(condensation, Condensation)
    condensation.action._id = 7
    state.history.append(condensation.action)
    assert condensation.action.forgotten_event_ids == [3]

    view = condenser.condenseWithState(state)
    assert isinstance(view, View)
    assert view.events == [first_message, assistant_message_event, condensation.action]

    messages = agent._get_messages(view.events)
    assert messages[0].role == 'system'
    assert 'You are OpenHands' in messages[0].content[0].text
    assert len(messages) == 3


def test_llm_agent_cache_condenser_first_message_user_message():
    """Do not allow the LLM to remove all conversation messages"""

    mock_llm = MagicMock(spec=LLM)
    mock_llm.is_caching_prompt_active.return_value = True
    mock_llm.config = MagicMock(max_message_chars=1000)
    mock_llm.vision_is_active.return_value = False
    mock_llm.metrics = MagicMock()
    mock_llm.metrics.get.return_value = {'tokens': 100}

    agent_config = AgentConfig()
    agent = LLMCacheCodeAgent(mock_llm, agent_config)

    condenser = agent.condenser

    first_message = MessageAction('Hello, how are you?')
    first_message._source = 'user'
    first_message._id = 1
    assistant_message_event = MessageAction('Great!')
    assistant_message_event._source = 'agent'
    assistant_message_event._id = 2
    user_condensation_message_event = MessageAction('NOW CONDENSE!')
    user_condensation_message_event._source = 'user'
    user_condensation_message_event._id = 3

    state = State(
        history=[
            first_message,
            assistant_message_event,
            user_condensation_message_event,
        ]
    )

    # Simulate the LLM response for condensation
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = 'KEEP: 0'
    mock_llm.completion.return_value = mock_response

    # Perform condensation
    condensation = condenser.condenseWithState(state)

    assert isinstance(condensation, Condensation)
    condensation.action._id = 7
    state.history.append(condensation.action)
    # Would be 1,2,3. But we put 1 back in so we have a message at least.
    assert condensation.action.forgotten_event_ids == [2, 3]

    view = condenser.condenseWithState(state)
    assert isinstance(view, View)
    assert view.events == [first_message, condensation.action]
