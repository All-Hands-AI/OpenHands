import asyncio

from opendevin.controller.agent import Agent
from opendevin.controller.state.state import State
from opendevin.core.config import LLMConfig
from opendevin.core.main import run_agent_controller
from opendevin.llm.llm import LLM
from tests.integration.test_agent import validate_final_state

max_iterations = 15
max_budget_per_task = 15


def test_dummy_agent(current_test_name: str):
    # Create the agent
    agent = Agent.get_cls('DummyAgent')(llm=LLM(LLMConfig()))

    # Execute the task
    task = 'Do nothing. Do not ask me for confirmation at any point.'
    final_state: State = asyncio.run(
        run_agent_controller(agent, task, max_iterations, max_budget_per_task)
    )
    validate_final_state(final_state, current_test_name)
