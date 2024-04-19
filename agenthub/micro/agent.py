import json
from typing import List

from jinja2 import Environment, BaseLoader

from opendevin.agent import Agent
from opendevin.llm.llm import LLM
from opendevin.state import State
from opendevin.action import Action, action_from_dict

from .instructions import instructions


def parse_response(response: str) -> Action:
    json_start = response.find('{')
    json_end = response.rfind('}') + 1
    response = response[json_start:json_end]
    action_dict = json.loads(response)
    action = action_from_dict(action_dict)
    return action


def my_encoder(obj):
    """
    Encodes objects as dictionaries

    Parameters:
    - obj (Object): An object that will be converted

    Returns:
    - dict: If the object can be converted it is returned in dict format
    """
    if hasattr(obj, 'to_dict'):
        return obj.to_dict()


def dumps(obj, **kwargs):
    """
    Serialize an object to str format
    """
    return json.dumps(obj, default=my_encoder, **kwargs)


class MicroAgent(Agent):
    def __init__(self, llm: LLM):
        super().__init__(llm)

    def initialize(self, agentDef, prompt):
        if 'name' not in agentDef:
            raise ValueError('Agent definition must contain a name')
        self.name = agentDef['name']
        self.description = agentDef['description'] if 'description' in agentDef else ''
        self.inputs = agentDef['inputs'] if 'inputs' in agentDef else []
        self.outputs = agentDef['outputs'] if 'outputs' in agentDef else []
        self.examples = agentDef['examples'] if 'examples' in agentDef else []
        self.prompt_template = Environment(loader=BaseLoader).from_string(prompt)

    def step(self, state: State) -> Action:
        prompt = self.prompt_template.render(state=state, instructions=instructions, to_json=dumps)
        messages = [{'content': prompt, 'role': 'user'}]
        resp = self.llm.completion(messages=messages)
        action_resp = resp['choices'][0]['message']['content']
        state.num_of_chars += len(prompt) + len(action_resp)
        action = parse_response(action_resp)
        return action

    def search_memory(self, query: str) -> List[str]:
        return []
