from unittest.mock import MagicMock

from openhands.agenthub.supervisor_agent.supervisor_agent import SupervisorAgent
from openhands.controller.state.state import State
from openhands.core.config.agent_config import AgentConfig
from openhands.events.action import MessageAction
from openhands.events.event import EventSource


def test_process_history_with_observations_delegated_state():
    """Test that process_history_with_observations correctly uses delegated_state from extra_data."""
    # Create a mock LLM
    mock_llm = MagicMock()

    # Create a mock config
    mock_config = MagicMock(spec=AgentConfig)

    # Create a SupervisorAgent
    agent = SupervisorAgent(llm=mock_llm, config=mock_config)

    # Create a parent state
    parent_state = State(session_id='parent-session')

    # Create a delegated state with some history
    delegated_state = State(session_id='delegated-session')

    # Add some events to the delegated state's history
    message_action1 = MessageAction(content='Hello from delegated agent')
    message_action1._source = EventSource.AGENT  # Set the source directly
    delegated_state.history.append(message_action1)

    message_action2 = MessageAction(content='User response')
    message_action2._source = EventSource.USER  # Set the source directly
    delegated_state.history.append(message_action2)

    # Store the delegated state in the parent state's extra_data
    parent_state.extra_data['delegated_state'] = delegated_state

    # Process the history
    result = agent.process_history_with_observations(parent_state)

    # Verify that the result contains the delegated agent's message
    assert 'Hello from delegated agent' in result


def test_process_history_with_observations_fallback():
    """Test that process_history_with_observations falls back to delegated_histories if delegated_state is not available."""
    # Create a mock LLM
    mock_llm = MagicMock()

    # Create a mock config
    mock_config = MagicMock(spec=AgentConfig)

    # Create a SupervisorAgent
    agent = SupervisorAgent(llm=mock_llm, config=mock_config)

    # Create a parent state
    parent_state = State(session_id='parent-session')

    # Create a delegated history
    delegated_history = []

    message_action1 = MessageAction(content='Hello from delegated history')
    message_action1._source = EventSource.AGENT  # Set the source directly
    delegated_history.append(message_action1)

    message_action2 = MessageAction(content='User response')
    message_action2._source = EventSource.USER  # Set the source directly
    delegated_history.append(message_action2)

    # Add the delegated history to the parent state's delegated_histories
    parent_state.delegated_histories.append(delegated_history)

    # Process the history
    result = agent.process_history_with_observations(parent_state)

    # Verify that the result contains the delegated history's message
    assert 'Hello from delegated history' in result


def test_process_history_with_observations_empty():
    """Test that process_history_with_observations handles empty delegated_state and delegated_histories."""
    # Create a mock LLM
    mock_llm = MagicMock()

    # Create a mock config
    mock_config = MagicMock(spec=AgentConfig)

    # Create a SupervisorAgent
    agent = SupervisorAgent(llm=mock_llm, config=mock_config)

    # Create a parent state
    parent_state = State(session_id='parent-session')

    # Process the history
    result = agent.process_history_with_observations(parent_state)

    # Verify that the result contains a message about no delegation event found
    assert 'No delegation event found in history' in result
