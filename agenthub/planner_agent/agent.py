from typing import List
from .prompt import get_prompt, parse_response

from opendevin.agent import Agent
from opendevin.action import AgentFinishAction
from opendevin.llm.llm import LLM
from opendevin.state import State
from opendevin.action import Action

class PlannerAgent(Agent):
    """
    The planner agent utilizes a special prompting strategy to create long term plans for solving problems.
    The agent is given its previous action-observation pairs, current task, and hint based on last action taken at every step.
    """

    def __init__(self, llm: LLM):
        """
        Initialize the Planner Agent with an LLM

        Parameters:
        - llm (LLM): The llm to be used by this agent
        """
        super().__init__(llm)

    def step(self, state: State) -> Action:
        """
        Checks to see if current step is completed, returns AgentFinishAction if True. 
        Otherwise, creates a plan prompt and sends to model for inference, returning the result as the next action.

        Parameters:
        - state (State): The current state given the previous actions and observations

        Returns:
        - AgentFinishAction: If the last state was 'completed', 'verified', or 'abandoned'
        - Action: The next action to take based on llm response
        """

        if state.plan.task.state in ['completed', 'verified', 'abandoned']:
            return AgentFinishAction()
        prompt = get_prompt(state.plan, state.history)
        messages = [{"content": prompt, "role": "user"}]
        resp = self.llm.completion(messages=messages)
        action_resp = resp['choices'][0]['message']['content']
        action = parse_response(action_resp)
        return action

    def search_memory(self, query: str) -> List[str]:
        return []

