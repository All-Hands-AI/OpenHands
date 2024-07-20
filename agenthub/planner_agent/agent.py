from agenthub.planner_agent.response_parser import PlannerResponseParser
from opendevin.controller.agent import Agent
from opendevin.controller.state.state import State
from opendevin.events.action import Action, AgentFinishAction
from opendevin.llm.llm import LLM
from opendevin.runtime.tools import RuntimeTool

from .prompt import get_prompt


class PlannerAgent(Agent):
    VERSION = '1.0'
    """
    The planner agent utilizes a special prompting strategy to create long term plans for solving problems.
    The agent is given its previous action-observation pairs, current task, and hint based on last action taken at every step.
    """
    runtime_tools: list[RuntimeTool] = [RuntimeTool.BROWSER]
    response_parser = PlannerResponseParser()

    def __init__(self, llm: LLM):
        """Initialize the Planner Agent with an LLM

        Parameters:
        - llm (LLM): The llm to be used by this agent
        """
        super().__init__(llm)

    def step(self, state: State) -> Action:
        """Checks to see if current step is completed, returns AgentFinishAction if True.
        Otherwise, creates a plan prompt and sends to model for inference, returning the result as the next action.

        Parameters:
        - state (State): The current state given the previous actions and observations

        Returns:
        - AgentFinishAction: If the last state was 'completed', 'verified', or 'abandoned'
        - Action: The next action to take based on llm response
        """
        if state.root_task.state in [
            'completed',
            'verified',
            'abandoned',
        ]:
            return AgentFinishAction()
        prompt = get_prompt(state, self.llm.config.max_message_chars)
        messages = [{'content': prompt, 'role': 'user'}]
        resp = self.llm.completion(messages=messages)
        return self.response_parser.parse(resp)
