import json
from typing import List, Dict

from jinja2 import Environment, BaseLoader

from opendevin.agent import Agent
from opendevin.llm.llm import LLM
from opendevin.state import State
from opendevin.action import Action, action_from_dict

from .instructions import instructions
from .registry import all_agents


def parse_response(orig_response: str) -> Action:
    json_start = orig_response.find('{')
    json_end = orig_response.rfind('}') + 1
    response = orig_response[json_start:json_end]
    try:
        action_dict = json.loads(response)
    except json.JSONDecodeError:
        # TODO: remove this debug stuff
        print('Invalid JSON in response')
        print(orig_response)
        raise ValueError('Invalid JSON in response')
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
    prompt = ''
    agentDefinition: Dict = {}

    def __init__(self, llm: LLM):
        super().__init__(llm)
        if 'name' not in self.agentDefinition:
            raise ValueError('Agent definition must contain a name')
        self.name = self.agentDefinition['name']
        self.description = self.agentDefinition['description'] if 'description' in self.agentDefinition else ''
        self.inputs = self.agentDefinition['inputs'] if 'inputs' in self.agentDefinition else []
        self.outputs = self.agentDefinition['outputs'] if 'outputs' in self.agentDefinition else []
        self.examples = self.agentDefinition['examples'] if 'examples' in self.agentDefinition else []
        self.prompt_template = Environment(loader=BaseLoader).from_string(self.prompt)
        self.delegates = all_agents.copy()
        del self.delegates[self.name]

    def step(self, state: State) -> Action:
        prompt = self.prompt_template.render(state=state, instructions=instructions, to_json=dumps, delegates=self.delegates)
        messages = [{'content': prompt, 'role': 'user'}]
        resp = self.llm.completion(messages=messages)
        action_resp = resp['choices'][0]['message']['content']
        state.num_of_chars += len(prompt) + len(action_resp)
        action = parse_response(action_resp)
        return action

    def search_memory(self, query: str) -> List[str]:
        return []
