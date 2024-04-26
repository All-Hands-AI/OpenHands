import asyncio

from agenthub.dummy_agent import DummyAgent

from opendevin.controller import AgentController
from opendevin.llm.llm import LLM


def test_actions_with_dummy_agent():
    llm = LLM('not-a-real-model')
    agent = DummyAgent(llm=llm)
    controller = AgentController(agent=agent)

    asyncio.run(controller.start('do a flip'))
    # assertions are inside the DummyAgent
