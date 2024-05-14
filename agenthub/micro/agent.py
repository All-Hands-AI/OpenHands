from jinja2 import BaseLoader, Environment

from opendevin.controller.agent import Agent
from opendevin.controller.state.state import State
from opendevin.core.utils import json
from opendevin.events.action import Action, action_from_dict
from opendevin.llm.llm import LLM

from .instructions import instructions
from .registry import all_microagents


def parse_response(orig_response: str) -> Action:
    # attempt to load the JSON dict from the response
    action_dict = json.loads(orig_response)

    # load the action from the dict
    return action_from_dict(action_dict)


def to_json(obj, **kwargs):
    """
    Serialize an object to str format
    """
    return json.dumps(obj, **kwargs)


class MicroAgent(Agent):
    prompt = ''
    agent_definition: dict = {}

    def __init__(self, llm: LLM):
        super().__init__(llm)
        if 'name' not in self.agent_definition:
            raise ValueError('Agent definition must contain a name')
        self.prompt_template = Environment(loader=BaseLoader).from_string(self.prompt)
        self.delegates = all_microagents.copy()
        del self.delegates[self.agent_definition['name']]

    def step(self, state: State) -> Action:
        latest_user_message = state.get_current_user_intent()
        prompt = self.prompt_template.render(
            state=state,
            instructions=instructions,
            to_json=to_json,
            delegates=self.delegates,
            latest_user_message=latest_user_message,
        )
        messages = [{'content': prompt, 'role': 'user'}]
        resp = self.llm.completion(messages=messages)
        action_resp = resp['choices'][0]['message']['content']
        state.num_of_chars += len(prompt) + len(action_resp)
        action = parse_response(action_resp)
        return action

    def search_memory(self, query: str) -> list[str]:
        return []
