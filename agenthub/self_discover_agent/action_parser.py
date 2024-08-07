import re

from opendevin.controller.action_parser import ActionParser, ResponseParser
from opendevin.core.utils import json
from opendevin.events.action import (
    Action,
    AgentDelegateAction,
    MessageAction,
)

from .prompt import RESEASONING_MODULE_LIST


def dict_to_bullet_points(d: dict, indent: int = 0):
    bullet_points = ''
    for key, value in d.items():
        bullet_points += '  ' * indent + f'- {key}\n'
        if isinstance(value, dict):
            bullet_points += dict_to_bullet_points(value, indent + 1)
        else:
            bullet_points += '  ' * (indent + 1) + f'- {value}\n'
    return bullet_points


class SelfDiscoverResponseParser(ResponseParser):
    """
    Parser action:
        - AgentDelegateAction(agent, inputs) - delegate action to BrowserAgent for browsing or CodeActAgent for plan execution
        - MessageAction(content) - Message action for user interaction if 'wait_for_response' == True
        - MessageAction(content) - Message action to advance to next self discovery state if 'wait_for_response' == False
    """

    def __init__(self):
        super().__init__()
        # Order matters as plan is considered last step
        self.action_parsers = [
            SelfDiscoverActionParserAskUser(),
            SelfDiscoverActionParserBrowserAgent(),
            SelfDiscoverActionParserExecutePlan(),
        ]
        self.default_parser = SelfDiscoverActionParserAdvance()

    def parse(self, response: str) -> Action:
        action_str = self.parse_response(response)
        return self.parse_action(action_str)

    def parse_response(self, response) -> str:
        action = response.choices[0].message.content
        if action is None:
            return ''
        for lang in ['ask', 'plan', 'browse']:
            if f'<execute_{lang}>' in action and f'</execute_{lang}>' not in action:
                action += f'</execute_{lang}>'
        return action

    def parse_action(self, action_str: str) -> Action:
        for action_parser in self.action_parsers:
            if action_parser.check_condition(action_str):
                return action_parser.parse(action_str)
        return self.default_parser.parse(action_str)


class SelfDiscoverActionParserExecutePlan(ActionParser):
    """
    Parser action:
        - AgentDelegateAction(agent, inputs) - delegate action for (sub)task
    """

    def __init__(
        self,
    ):
        self.plan_command = None

    def check_condition(self, action_str: str) -> bool:
        self.plan_command = re.search(
            r'<execute_plan>(.*)</execute_plan>', action_str, re.DOTALL
        )
        return self.plan_command is not None

    def parse(self, action_str: str) -> Action:
        assert (
            self.plan_command is not None
        ), 'self.delegate_command should not be None when parse is called'
        thought = action_str.replace(self.plan_command.group(0), '').strip()
        task = self.plan_command.group(1).strip()
        formatted_thought = thought + f'\n\n{task}'
        return AgentDelegateAction(
            agent='CodeActAgent', inputs={'task': task}, thought=formatted_thought
        )


class SelfDiscoverActionParserBrowserAgent(ActionParser):
    """
    Parser action:
        - AgentDelegateAction(agent, inputs) - delegate action for (sub)task
    """

    def __init__(
        self,
    ):
        self.browse_command = None

    def check_condition(self, action_str: str) -> bool:
        self.browse_command = re.search(
            r'<execute_browse>(.*)</execute_browse>', action_str, re.DOTALL
        )
        return self.browse_command is not None

    def parse(self, action_str: str) -> Action:
        assert (
            self.browse_command is not None
        ), 'self.browse_command should not be None when parse is called'
        thought = action_str.replace(self.browse_command.group(0), '').strip()
        browse_actions = self.browse_command.group(1).strip()
        task = f'{thought}. I should start with: {browse_actions}'
        return AgentDelegateAction(agent='BrowsingAgent', inputs={'task': task})


class SelfDiscoverActionParserAdvance(ActionParser):
    """
    Parser action:
        - MessageAction(content) - Message action to run (e.g. ask for clarification)
    """

    def __init__(
        self,
    ):
        pass

    def check_condition(self, action_str: str) -> bool:
        # We assume the LLM is GOOD enough that when it returns JSON/pure natural language
        # we can go to the next step of the self discovery
        return True

    def parse(self, action_str: str) -> Action:
        action_dict = json.loads(action_str)

        if (
            'selected_reasoning_modules' in action_dict
            and action_dict['selected_reasoning_modules']
        ):
            content = 'To solve the given task I selected the following candidate reasoning modules:\n\n'
            # content += "<ul>" + "\n".join([f"<li>{RESEASONING_MODULE_LIST[i]}</li>" for i in action_dict["selected_reasoning_modules"]]) + "</ul>"
            content += '\n'.join(
                f'* {RESEASONING_MODULE_LIST[i]}'
                for i in action_dict['selected_reasoning_modules']
            )
        elif (
            'adapted_reasoning_modules' in action_dict
            and action_dict['adapted_reasoning_modules']
        ):
            content = 'I have adapted the selected candidate reasoning modules to the given task as follows:\n'
            print(action_dict['adapted_reasoning_modules'])
            # content += dict_to_bullet_points(action_dict["adapted_reasoning_modules"])
        else:
            content = ''
        # content = action_str
        return MessageAction(content=content)


class SelfDiscoverActionParserAskUser(ActionParser):
    """
    Parser action:
        - MessageAction(content) - Message action to run (e.g. ask for clarification)
    """

    def __init__(
        self,
    ):
        self.ask_command = None

    def check_condition(self, action_str: str) -> bool:
        self.ask_command = re.search(
            r'<execute_ask>(.*)</execute_ask>', action_str, re.DOTALL
        )
        return self.ask_command is not None

    def parse(self, action_str: str) -> Action:
        assert (
            self.ask_command is not None
        ), 'self.agent_ask should not be None when parse is called'
        thought = action_str.replace(self.ask_command.group(0), '').strip()
        ask = self.ask_command.group(1).strip()
        content = f'{thought} {ask}'
        return MessageAction(content=content, wait_for_response=True)
