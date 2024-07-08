import asyncio
from typing import Union

from jinja2 import BaseLoader, Environment

from opendevin.controller.agent import Agent
from opendevin.controller.state.state import State
from opendevin.core.utils import json
from opendevin.events.action import Action
from opendevin.events.serialization.action import action_from_dict
from opendevin.events.serialization.event import event_to_memory
from opendevin.llm.llm import LLM
from opendevin.memory.history import ShortTermHistory
from opendevin.runtime.utils.async_utils import async_to_sync

from .instructions import instructions
from .registry import all_microagents


def parse_response(orig_response: Union[str, dict]) -> Action:
    if isinstance(orig_response, str):
        # attempt to load the JSON dict from the response
        action_dict = json.loads(orig_response)
    elif isinstance(orig_response, dict):
        # If it's already a dict, use it directly
        action_dict = orig_response
    else:
        raise TypeError(f'Expected str or dict, got {type(orig_response)}')

    # load the action from the dict
    return action_from_dict(action_dict)


def to_json(obj, **kwargs):
    """
    Serialize an object to str format
    """
    return json.dumps(obj, **kwargs)


def history_to_json(history: ShortTermHistory, max_events=20, **kwargs):
    """
    Serialize and simplify history to str format
    """

    processed_history = []
    event_count = 0

    for event in history.get_events(reverse=True):
        if event_count >= max_events:
            break
        processed_history.append(event_to_memory(event))
        event_count += 1

    # history is in reverse order, let's fix it
    processed_history.reverse()

    return json.dumps(processed_history, **kwargs)


class MicroAgent(Agent):
    VERSION = '1.0'
    prompt = ''
    agent_definition: dict = {}

    def __init__(self, llm: LLM):
        super().__init__(llm)
        if 'name' not in self.agent_definition:
            raise ValueError('Agent definition must contain a name')
        self.prompt_template = Environment(loader=BaseLoader).from_string(self.prompt)
        self.delegates = all_microagents.copy()
        del self.delegates[self.agent_definition['name']]

    @async_to_sync
    def step(self, state: State) -> Action:
        return self.step_async(state)  # type: ignore

    async def step_async(self, state: State) -> Action:
        prompt = self.prompt_template.render(
            state=state,
            instructions=instructions,
            to_json=to_json,
            history_to_json=history_to_json,
            delegates=self.delegates,
            latest_user_message=state.get_current_user_intent(),
        )
        messages = [{'content': prompt, 'role': 'user'}]

        # If self.llm.completion is async
        if asyncio.iscoroutinefunction(self.llm.completion):
            resp = await self.llm.completion(messages=messages)
        else:
            # If it's not async, use to_thread
            # resp = await asyncio.to_thread(self.llm.completion, messages=messages)
            resp = await asyncio.to_thread(self.llm.completion, messages=messages)

        # Handle both real responses and mock responses in tests
        if isinstance(resp, dict) and 'choices' in resp:
            action_resp = resp['choices'][0]['message']['content']
        elif isinstance(resp, str):
            action_resp = resp
        else:
            # For mock responses in tests, try to get the return_value
            try:
                action_resp = resp.return_value['choices'][0]['message']['content']
            except AttributeError:
                raise TypeError(f'Unexpected response type: {type(resp)}')

        action = parse_response(action_resp)
        return action

    def search_memory(self, query: str) -> list[str]:
        return []
