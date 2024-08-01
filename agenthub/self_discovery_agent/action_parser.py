import re

from opendevin.controller.action_parser import ActionParser, ResponseParser
from opendevin.events.action import (
    Action,
    AgentDelegateAction,
    MessageAction,
)


class SelfDiscoverResponseParser(ResponseParser):
    """
    Parser action:
        - AgentDelegateAction(agent, inputs) - delegate action to BrowserAgent for browsing or CodeActAgent for plan execution
        - MessageAction(content) - Message action for user interaction
        - MessageAction(content) - Message action to advance to next step of self discovery
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
        plan = self.plan_command.group(1).strip()
        task = f'{thought}. Execute the following plan:\n{plan}'
        return AgentDelegateAction(agent='CodeActAgent', inputs={'task': task})


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
        # We assume the LLM is GOOD enough that when it returns pure natural language
        # we can go to the next step of the self discovery
        return True

    def parse(self, action_str: str) -> Action:
        return MessageAction(content=action_str)


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
