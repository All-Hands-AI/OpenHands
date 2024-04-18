from typing import List

from jinja2 import Environment, BaseLoader

from opendevin.agent import Agent
from opendevin.llm.llm import LLM
from opendevin.state import State
from opendevin.action import Action

from .instructions import instructions

class MicroAgent(Agent):
    def __init__(self, llm: LLM):
        super().__init__(llm)

    def initialize(self, agentDef, prompt):
        self.name = agentDef['name']
        self.description = agentDef['description']
        self.inputs = agentDef['inputs']
        self.outputs = agentDef['outputs']
        self.examples = agentDef['examples']
        self.prompt_template = Environment(loader=BaseLoader).from_string(prompt)

    def step(self, state: State) -> Action:
        prompt = self.prompt_template.render(state=state, instructions=all_instructions)
        messages = [{'content': prompt, 'role': 'user'}]
        resp = self.llm.completion(messages=messages)
        action_resp = resp['choices'][0]['message']['content']
        state.num_of_chars += len(prompt) + len(action_resp)
        action = parse_response(action_resp)
        return action

    def search_memory(self, query: str) -> List[str]:
        return []
