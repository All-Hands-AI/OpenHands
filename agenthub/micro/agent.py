import json
from typing import Dict, List

from jinja2 import BaseLoader, Environment

from opendevin.controller.agent import Agent
from opendevin.controller.state.state import State
from opendevin.core.exceptions import LLMOutputError
from opendevin.events.action import Action, action_from_dict
from opendevin.llm.llm import LLM

from .instructions import instructions
from .registry import all_microagents


def parse_response(orig_response: str) -> Action:
    json_start = orig_response.find('{')
    json_end = orig_response.rfind('}') + 1
    response = orig_response[json_start:json_end]
    try:
        action_dict = json.loads(response)
    except json.JSONDecodeError as e:
        raise LLMOutputError(
            'Invalid JSON in response. Please make sure the response is a valid JSON object'
        ) from e
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


def to_json(obj, **kwargs):
    """
    Serialize an object to str format
    """
    return json.dumps(obj, default=my_encoder, **kwargs)


class MicroAgent(Agent):
    prompt = ''
    agent_definition: Dict = {}

    def __init__(self, llm: LLM):
        super().__init__(llm)
        if 'name' not in self.agent_definition:
            raise ValueError('Agent definition must contain a name')
        self.prompt_template = Environment(loader=BaseLoader).from_string(self.prompt)
        self.delegates = all_microagents.copy()
        del self.delegates[self.agent_definition['name']]

    def step(self, state: State) -> Action:
        prompt = self.prompt_template.render(
            state=state,
            instructions=instructions,
            to_json=to_json,
            delegates=self.delegates,
        )
        messages = [{'content': prompt, 'role': 'user'}]
        resp = self.llm.completion(messages=messages)
        action_resp = resp['choices'][0]['message']['content']
        state.num_of_chars += len(prompt) + len(action_resp)
        action = parse_response(action_resp)
        return action

    def search_memory(self, query: str) -> List[str]:
        return []
