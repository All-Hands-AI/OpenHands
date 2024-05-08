import json
from typing import Dict, List

from jinja2 import BaseLoader, Environment

from opendevin.controller.agent import Agent
from opendevin.controller.state.state import State
from opendevin.core.exceptions import LLMOutputError
from opendevin.events.action import Action, AgentFinishAction, action_from_dict
from opendevin.llm.llm import LLM

from .instructions import instructions
from .registry import all_microagents


def parse_response(orig_response: str) -> Action:
    depth = 0
    start = -1
    for i, char in enumerate(orig_response):
        if char == '{':
            if depth == 0:
                start = i
            depth += 1
        elif char == '}':
            depth -= 1
            if depth == 0 and start != -1:
                response = orig_response[start : i + 1]
                try:
                    action_dict = json.loads(response)
                    action = action_from_dict(action_dict)
                    return action
                except json.JSONDecodeError as e:
                    raise LLMOutputError(
                        'Invalid JSON in response. Please make sure the response is a valid JSON object.'
                    ) from e
    raise LLMOutputError('No valid JSON object found in response.')


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
        self.delegates = all_microagents.copy()
        del self.delegates[self.agent_definition['name']]

    def prompt_to_action(self, prompt: str, state: State) -> Action:
        template = Environment(loader=BaseLoader).from_string(prompt)
        rendered = template.render(
            state=state,
            instructions=instructions,
            to_json=to_json,
            delegates=self.delegates,
        )
        messages = [{'content': rendered, 'role': 'user'}]
        resp = self.llm.completion(messages=messages)
        action_resp = resp['choices'][0]['message']['content']
        state.num_of_chars += len(prompt) + len(action_resp)
        action = parse_response(action_resp)
        return action

    def step(self, state: State) -> Action:
        if 'workflow' in self.agent_definition:
            return self.step_workflow(state)
        return self.prompt_to_action(self.prompt, state)

    def step_workflow(self, state: State) -> Action:
        if state.iteration >= len(self.agent_definition['workflow']):
            return AgentFinishAction()
        step = self.agent_definition['workflow'][state.iteration]
        if 'action' in step:
            action = action_from_dict(step['action'])
            return action
        elif 'prompt' in step:
            prompt = step['prompt']
            if step['prompt'].endswith('.md'):
                with open(prompt, 'r') as f:
                    prompt = f.read()
            return self.prompt_to_action(prompt, state)
        else:
            raise ValueError('Step must contain either an action or a prompt')

    def search_memory(self, query: str) -> List[str]:
        return []
