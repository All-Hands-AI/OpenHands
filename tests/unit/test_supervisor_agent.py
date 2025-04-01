import pytest

from openhands.agenthub.supervisor_agent import SupervisorAgent
from openhands.controller.state.state import State
from openhands.core.config import AgentConfig, LLMConfig
from openhands.events.action import (
    AgentDelegateAction,
    AgentFinishAction,
    AgentFinishTaskCompleted,
    MessageAction,
)
from openhands.events.event import EventSource
from openhands.events.observation import (
    AgentDelegateObservation,
    CmdOutputObservation,
    FileReadObservation,
)
from openhands.llm.llm import LLM


class TestSupervisorAgent:
    @pytest.fixture
    def agent(self):
        llm_config = LLMConfig(model='test-model', api_key='test-key')
        llm = LLM(config=llm_config)
        config = AgentConfig()
        return SupervisorAgent(llm=llm, config=config)

    def test_initial_delegation(self, agent):
        """Test that the agent delegates to CodeActAgent on the first step."""
        state = State(session_id='test', inputs={'test': 'value'})
        action = agent.step(state)

        assert isinstance(action, AgentDelegateAction)
        assert action.agent == 'CodeActAgent'
        assert action.inputs == state.inputs

    def test_finish_after_delegation_complete(self, agent):
        """Test that the agent finishes when the delegated agent is done."""
        state = State(session_id='test', inputs={'test': 'value'})

        # First step - should delegate
        action = agent.step(state)
        assert isinstance(action, AgentDelegateAction)

        # Add a delegate observation to the history
        observation = AgentDelegateObservation(outputs={}, content='Task completed')
        observation.action = 'delegate_observation'  # Add the action attribute
        state.history.append(observation)

        # Second step - should finish
        action = agent.step(state)
        assert isinstance(action, AgentFinishAction)
        assert action.task_completed == AgentFinishTaskCompleted.TRUE

    def test_history_processing(self, agent):
        """Test that the agent processes the history of actions and observations."""
        state = State(session_id='test', inputs={'test': 'value'})

        # Add a user message to the history
        user_message = MessageAction(
            content='Please help me with this task',
        )
        user_message._source = EventSource.USER  # Set the source directly
        state.history.append(user_message)

        # First step - should delegate
        action = agent.step(state)
        assert isinstance(action, AgentDelegateAction)

        # Add some agent messages and observations to simulate CodeActAgent activity
        agent_message1 = MessageAction(
            content="I'll help you with this task. Let me check the files first.",
        )
        agent_message1._source = EventSource.AGENT  # Set the source directly
        state.history.append(agent_message1)

        file_observation = FileReadObservation(
            content='This is the content of the file',
            path='/path/to/file.txt',
        )
        state.history.append(file_observation)

        agent_message2 = MessageAction(
            content='I found the file. Now let me run a command.',
        )
        agent_message2._source = EventSource.AGENT  # Set the source directly
        state.history.append(agent_message2)

        cmd_observation = CmdOutputObservation(
            content='Command executed successfully',
            exit_code=0,
            command='ls -la',
        )
        state.history.append(cmd_observation)

        agent_message3 = MessageAction(
            content='Task completed successfully!',
        )
        agent_message3._source = EventSource.AGENT  # Set the source directly
        state.history.append(agent_message3)

        # Add a delegate observation to the history
        observation = AgentDelegateObservation(outputs={}, content='Task completed')
        observation.action = 'delegate_observation'  # Add the action attribute
        state.history.append(observation)

        # Second step - should finish and process history
        action = agent.step(state)
        assert isinstance(action, AgentFinishAction)
        assert action.task_completed == AgentFinishTaskCompleted.TRUE

        # Check that the processed history is stored in state.extra_data
        assert 'processed_history' in state.extra_data
        processed_history = state.extra_data['processed_history']

        # Check that the processed history contains the expected sections
        assert 'INITIAL ISSUE:' in processed_history
        assert 'Please help me with this task' in processed_history
        assert 'RESPONSE:' in processed_history
        assert 'OBSERVATION' in processed_history
        assert 'LAST RESPONSE:' in processed_history
        assert 'FINISH REASON:' in processed_history

    def test_get_descriptive_finish_reason(self, agent):
        """Test the get_descriptive_finish_reason method."""
        assert (
            agent.get_descriptive_finish_reason('stop') == 'FINISHED_WITH_STOP_ACTION'
        )
        assert (
            agent.get_descriptive_finish_reason('tool_calls')
            == 'FINISHED_WITH_FUNCTION_CALL'
        )
        assert agent.get_descriptive_finish_reason('length') == 'EXCEEDED_MAX_LENGTH'
        assert (
            agent.get_descriptive_finish_reason('content_filter') == 'CONTENT_FILTERED'
        )
        assert (
            agent.get_descriptive_finish_reason('budget_exceeded') == 'BUDGET_EXCEEDED'
        )
        assert agent.get_descriptive_finish_reason('unknown') == 'UNKNOWN'
