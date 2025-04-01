import pytest

from openhands.agenthub.supervisor_agent import SupervisorAgent
from openhands.controller.state.state import State
from openhands.core.config import AgentConfig, LLMConfig
from openhands.events.action import (
    AgentDelegateAction,
    AgentFinishAction,
    AgentFinishTaskCompleted,
)
from openhands.events.observation import AgentDelegateObservation
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
