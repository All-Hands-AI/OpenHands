from openhands.controller.action_parser import ResponseParser
from openhands.core.utils import json
from openhands.events.action import (
    Action,
)
from openhands.events.serialization.action import action_from_dict


class PlannerResponseParser(ResponseParser):
    def __init__(self):
        super().__init__()

    def parse(self, response: str) -> Action:
        action_str = self.parse_response(response)
        return self.parse_action(action_str)

    def parse_response(self, response) -> str:
        # get the next action from the response
        return response['choices'][0]['message']['content']

    def parse_action(self, action_str: str) -> Action:
        """Parses a string to find an action within it

        Parameters:
        - response (str): The string to be parsed

        Returns:
        - Action: The action that was found in the response string
        """
        # attempt to load the JSON dict from the response
        action_dict = json.loads(action_str)

        if 'content' in action_dict:
            # The LLM gets confused here. Might as well be robust
            action_dict['contents'] = action_dict.pop('content')

        return action_from_dict(action_dict)
