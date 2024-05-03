
from typing import List

import agenthub.micromanager_agent.utils.prompts as prompts
from agenthub.micromanager_agent.utils.working_memory import WorkingMemory
from opendevin.controller.state.state import State
from opendevin.core import config
from opendevin.core.schema.config import ConfigType
from opendevin.events.action import (
    Action,
)
from opendevin.llm.llm import LLM

if config.get(ConfigType.AGENT_MEMORY_ENABLED):
    from agenthub.monologue_agent.utils.memory import LongTermMemory

    from typing import List

from opendevin.controller.state.state import State
from opendevin.events.action import Action
from opendevin.llm.llm import LLM
from opendevin.controller.agent import Agent

class MicroManagerAgent(Agent):
    llm: LLM
    goal: str
    working_memory: WorkingMemory
    memory: 'LongTermMemory | None'
    
    def __init__(self, llm: LLM):
        """
        Initializes the MicroManager Agent with an llm, and working memory.

        Parameters:
        - llm (LLM): The llm to be used by this agent
        """
        super().__init__(llm)

        self.working_memory = WorkingMemory(
            goal='Open Minded'
        )


    def step(self, state: State) -> Action:
        """
        Modifies the current state by adding the most recent actions and observations, then prompts the model to think about it's next action to take using monologue, memory, and hint.

        Parameters:
        - state (State): The current state based on previous steps taken

        Returns:
        - Action: The next action to take based on LLM response
        """
        
        # Not sure if this is necessary
        if state.plan.main_goal != self.goal:
            self.goal = state.plan.main_goal
            self.working_memory.goal = self.goal

        # Get the action
        prompt = prompts.get_request_action_prompt(
            state.plan.main_goal,
            self.working_memory.render(),
            state.background_commands_obs,
        )
        messages = [{'content': prompt, 'role': 'user'}]
        resp = self.llm.completion(messages=messages)
        action_resp = resp['choices'][0]['message']['content']
        state.num_of_chars += len(prompt) + len(action_resp)
        action = prompts.parse_action_response(action_resp)

        # Process and then ignore updated_info
        for prev_action, obs in state.updated_info:
            self.working_memory.orient(prev_action, obs, self.llm)
        state.updated_info = []
        return action
    
    def search_memory(self, query: str) -> List[str]:
        """
        Uses VectorIndexRetriever to find related memories within the long term memory.
        Uses search to produce top 10 results.

        Parameters:
        - query (str): The query that we want to find related memories for

        Returns:
        - List[str]: A list of top 10 text results that matched the query
        """
        if self.memory is None:
            return []
        return self.memory.search(query)
    
    def reset(self) -> None:
        super().reset()

        # Reset the working memory
        self._initialized = False