from openhands.agenthub.supervisor_agent.supervisor_agent import SupervisorAgent
from openhands.controller.state.state import State
from openhands.core.schema import ActionType
from openhands.events.action import MessageAction
from openhands.events.action.agent import AgentDelegateAction
from openhands.events.event import EventSource
from openhands.events.observation.delegate import AgentDelegateObservation


class TestDelegatedHistories:
    """Tests for the delegated_histories feature in State and SupervisorAgent."""

    def test_empty_delegated_histories(self):
        """Test that SupervisorAgent handles empty delegated_histories correctly."""
        state = State()
        state.delegated_histories = []

        # Create a mock delegation event
        delegate_event = AgentDelegateAction(
            agent='TestAgent',
            inputs={},
            thought='Delegating to TestAgent',
            action=ActionType.DELEGATE,
            clear_history=True,
        )

        # Add the delegation event to the history
        state.history.append(delegate_event)

        # Add a mock observation event after delegation
        observation_event = AgentDelegateObservation(
            content='TestAgent finishes task',
            outputs={},
            observation=EventSource.DELEGATE,
        )
        state.history.append(observation_event)

        # Create a SupervisorAgent instance
        supervisor = SupervisorAgent()

        # Process the history
        result = supervisor.process_history_with_observations(state)

        # Verify that the fallback method was used
        assert (
            'Processing 1 events after delegation' in result
            or 'No delegation event found in history' in result
        )

    def test_non_empty_delegated_histories(self):
        """Test that SupervisorAgent uses non-empty delegated_histories correctly."""
        state = State()

        # Create a mock delegated history with a message event
        message_event = MessageAction(
            content='This is a test message', source=EventSource.AGENT
        )

        # Add the message event to delegated_histories
        state.delegated_histories = [[message_event]]

        # Create a SupervisorAgent instance
        supervisor = SupervisorAgent()

        # Process the history
        result = supervisor.process_history_with_observations(state)

        # Verify that the delegated history was used
        assert 'Using delegated history at index 0 with 1 events' in result

    def test_missing_delegated_histories_attribute(self):
        """Test that SupervisorAgent handles missing delegated_histories attribute correctly."""
        state = State()

        # Remove the delegated_histories attribute
        delattr(state, 'delegated_histories')

        # Create a mock delegation event
        delegate_event = AgentDelegateAction(
            agent='TestAgent',
            inputs={},
            thought='Delegating to TestAgent',
            action=ActionType.DELEGATE,
            clear_history=True,
        )

        # Add the delegation event to the history
        state.history.append(delegate_event)

        # Create a SupervisorAgent instance
        supervisor = SupervisorAgent()

        # Process the history
        result = supervisor.process_history_with_observations(state)

        # Verify that the fallback method was used
        assert 'No delegated histories found in state' in result

    def test_multiple_delegations(self):
        """Test that SupervisorAgent handles multiple delegations correctly."""
        state = State()

        # Create mock delegated histories for multiple agents
        agent1_message = MessageAction(
            content='Message from Agent1', source=EventSource.AGENT
        )

        agent2_message = MessageAction(
            content='Message from Agent2', source=EventSource.AGENT
        )

        # Add the message events to delegated_histories
        state.delegated_histories = [
            [agent1_message],  # Agent1's history
            [agent2_message],  # Agent2's history
        ]

        # Create a SupervisorAgent instance
        supervisor = SupervisorAgent()

        # Process the history
        result = supervisor.process_history_with_observations(state)

        # Verify that the most recent delegated history was used
        assert 'Using delegated history at index 1 with 1 events' in result
