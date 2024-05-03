import agenthub.monologue_agent.utils.json as json
import agenthub.micromanager_agent.utils.prompts as prompts
from opendevin.core.exceptions import AgentEventTypeError
from opendevin.core.logger import opendevin_logger as logger
from opendevin.llm.llm import LLM
from typing import Dict, Union, List, Literal

class WorkingMemory:
    """
    We use the working memory as a way to keep track of the agent's state in a structured way.
    """
    goal: str
    event_log: List[Dict[str,str]]
    working_subgoal: str
    working_subplan: str# -1th index is the current goal, penultimate is the previous goal, etc.

    def __init__(self, goal: str):
        """
        Initialize the empty list of thoughts
        """
        self.working_subgoal = "Open Minded"
        self.working_subplan = "Open Minded"
        self.event_log = []

    def orient(self, action, observation, llm:LLM):
        """
        Orient the working memory based on the action and observation

        Parameters:
        - action (Action): The action taken
        - observation (Observation): The observation from the action
        """
        #self.event_log.append({'action': action, 'observation': observation})

        prompt = prompts.get_orient_to_working_memory_prompt(
            action, observation, self.event_log[:-5][::-1], self.working_subplan, self.working_subgoal
        )
        messages = [{'content': prompt, 'role': 'user'}]
        resp = llm.completion(messages=messages)
        orientation, working_subplan, working_subgoal = prompts.parse_orient_response(resp['choices'][0]['message']['content'])
        self.event_log.append({'action': action, 'observation': observation, 'orientation': orientation})
        if working_subplan:
            self.working_subplan = working_subplan
        if working_subgoal:
            self.working_subgoal = working_subgoal

    def render(self) -> str:

        """
        Renders the working memory to a string

        Returns:
        - str: The working memory as a string
        """
        working_memory_rendered = f"""
# Your Last Action, Observation, and Orientation
## Action\n{self.event_log[-1]['action']}
## Observation\n{self.event_log[-1]['observation']}
## Orientation\n{self.event_log[-1]['orientation']}

# Your Working Subplan and Subgoal
## Subplan\n{self.working_subplan}
## Subgoal\n{self.working_subgoal}

# Your Event Log (5 Events to the Last Action)
"""
        for i in range(-5,-1):
           working_memory_rendered += f"""
## Event {i+6}
### Action\n{self.event_log[i]['action']}
### Observation\n{self.event_log[i]['observation']}
### Orientation\n{self.event_log[i]['orientation']}
"""
        return working_memory_rendered