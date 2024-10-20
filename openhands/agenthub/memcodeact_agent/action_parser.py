import re

from openhands.controller.action_parser import ActionParser, ResponseParser
from openhands.events.action import (
    Action,
    AgentDelegateAction,
    AgentFinishAction,
    CmdRunAction,
    IPythonRunCellAction,
    MessageAction,
)
from openhands.events.action.agent import AgentSummarizeAction


class MemCodeActResponseParser(ResponseParser):
    """Parser actions for MemCodeActAgent:
    - CmdRunAction(command) - bash command to run
    - IPythonRunCellAction(code) - IPython code to run
    - AgentDelegateAction(agent, inputs) - delegate action for (sub)task
    - MessageAction(content) - Message action to run (e.g. ask for clarification)
    - AgentFinishAction() - end the interaction
    """

    def __init__(self):
        super().__init__()
        self.action_parsers = [
            MemCodeActActionParserFinish(),
            MemCodeActActionParserCmdRun(),
            MemCodeActActionParserIPythonRunCell(),
            MemCodeActActionParserAgentDelegate(),
        ]
        self.default_parser = MemCodeActActionParserMessage()

    def parse(self, response) -> Action:
        action_str = self.parse_response(response)
        return self.parse_action(action_str)

    def parse_response(self, response) -> str:
        action = response.choices[0].message.content
        if action is None:
            return ''

        # execute actions
        for lang in ['bash', 'ipython', 'browse']:
            # special handling for DeepSeek: it has the stop-word bug and returns </execute_ipython instead of </execute_ipython>
            if f'</execute_{lang}' in action and f'</execute_{lang}>' not in action:
                action = action.replace(f'</execute_{lang}', f'</execute_{lang}>')

            if f'<execute_{lang}>' in action and f'</execute_{lang}>' not in action:
                action += f'</execute_{lang}>'

        # memory actions
        for action in ['summarize', 'recall', 'add']:
            # the stop-word bug
            if f'<memory_{action}>' in action and f'</memory_{action}>' not in action:
                action += f'</memory_{action}>'

            if f'<memory_{action}>' in action and f'</memory_{action}>' not in action:
                action += f'</memory_{action}>'

        return action

    def parse_action(self, action_str: str) -> Action:
        for action_parser in self.action_parsers:
            if action_parser.check_condition(action_str):
                return action_parser.parse(action_str)
        return self.default_parser.parse(action_str)


class MemCodeActActionParserFinish(ActionParser):
    """Parser action:
    - AgentFinishAction() - end the interaction
    """

    def __init__(
        self,
    ):
        self.finish_command = None

    def check_condition(self, action_str: str) -> bool:
        self.finish_command = re.search(r'<finish>.*</finish>', action_str, re.DOTALL)
        return self.finish_command is not None

    def parse(self, action_str: str) -> Action:
        assert (
            self.finish_command is not None
        ), 'self.finish_command should not be None when parse is called'
        thought = action_str.replace(self.finish_command.group(0), '').strip()
        return AgentFinishAction(thought=thought)


class MemCodeActActionParserCmdRun(ActionParser):
    """Parser action:
    - CmdRunAction(command) - bash command to run
    - AgentFinishAction() - end the interaction
    """

    def __init__(
        self,
    ):
        self.bash_command = None

    def check_condition(self, action_str: str) -> bool:
        self.bash_command = re.search(
            r'<execute_bash>(.*?)</execute_bash>', action_str, re.DOTALL
        )
        return self.bash_command is not None

    def parse(self, action_str: str) -> Action:
        assert (
            self.bash_command is not None
        ), 'self.bash_command should not be None when parse is called'
        thought = action_str.replace(self.bash_command.group(0), '').strip()
        # a command was found
        command_group = self.bash_command.group(1).strip()
        if command_group.strip() == 'exit':
            return AgentFinishAction(thought=thought)
        return CmdRunAction(command=command_group, thought=thought)


class MemCodeActActionParserIPythonRunCell(ActionParser):
    """Parser action:
    - IPythonRunCellAction(code) - IPython code to run
    """

    def __init__(
        self,
    ):
        self.python_code = None
        self.jupyter_kernel_init_code: str = 'from agentskills import *'

    def check_condition(self, action_str: str) -> bool:
        self.python_code = re.search(
            r'<execute_ipython>(.*?)</execute_ipython>', action_str, re.DOTALL
        )
        return self.python_code is not None

    def parse(self, action_str: str) -> Action:
        assert (
            self.python_code is not None
        ), 'self.python_code should not be None when parse is called'
        code_group = self.python_code.group(1).strip()
        thought = action_str.replace(self.python_code.group(0), '').strip()
        return IPythonRunCellAction(
            code=code_group,
            thought=thought,
            kernel_init_code=self.jupyter_kernel_init_code,
        )


class MemCodeActActionParserAgentDelegate(ActionParser):
    """Parser action:
    - AgentDelegateAction(agent, inputs) - delegate action for (sub)task
    """

    def __init__(
        self,
    ):
        self.agent_delegate = None

    def check_condition(self, action_str: str) -> bool:
        self.agent_delegate = re.search(
            r'<execute_browse>(.*)</execute_browse>', action_str, re.DOTALL
        )
        return self.agent_delegate is not None

    def parse(self, action_str: str) -> Action:
        assert (
            self.agent_delegate is not None
        ), 'self.agent_delegate should not be None when parse is called'
        thought = action_str.replace(self.agent_delegate.group(0), '').strip()
        browse_actions = self.agent_delegate.group(1).strip()
        task = f'{thought}. I should start with: {browse_actions}'
        return AgentDelegateAction(agent='BrowsingAgent', inputs={'task': task})


class MemCodeActActionParserMessage(ActionParser):
    """Parser action:
    - MessageAction(content) - Message action to run (e.g. ask for clarification)
    """

    def __init__(
        self,
    ):
        pass

    def check_condition(self, action_str: str) -> bool:
        # We assume the LLM is GOOD enough that when it returns pure natural language
        # it wants to talk to the user
        return True

    def parse(self, action_str: str) -> Action:
        return MessageAction(content=action_str, wait_for_response=True)


class MemCodeActActionParserMemoryRecall(ActionParser):
    """Parser action:
    - RecallAction(query) - memory action to run
    """

    def __init__(self):
        self.query = None

    def check_condition(self, action_str: str) -> bool:
        self.query = re.search(
            r'<memory_recall>(.*?)</memory_recall>', action_str, re.DOTALL
        )
        return self.query is not None

    def parse(self, action_str: str) -> Action:
        assert (
            self.query is not None
        ), 'self.query should not be None when parse is called'

        # <memory_recall>query</memory_recall>
        thought = action_str.replace(self.query.group(0), '').strip()
        return RecallAction(query=self.query.group(1).strip(), thought=thought)


class MemCodeActActionParserMemoryAdd(ActionParser):
    """Parser action:
    - AddAction(content) - memory action to run
    """

    def __init__(self):
        self.content = None

    def check_condition(self, action_str: str) -> bool:
        self.content = re.search(
            r'<memory_add>(.*?)</memory_add>', action_str, re.DOTALL
        )
        return self.content is not None

    def parse(self, action_str: str) -> Action:
        assert (
            self.content is not None
        ), 'self.content should not be None when parse is called'

        # <memory_add>content</memory_add>
        thought = action_str.replace(self.content.group(0), '').strip()
        return AddAction(content=self.content.group(1).strip(), thought=thought)


class MemCodeActActionParserMemorySummarize(ActionParser):
    """Parser action:
    - SummarizeAction(query) - memory action to run
    """

    def __init__(self):
        self.query = None

    def check_condition(self, action_str: str) -> bool:
        self.query = re.search(
            r'<memory_summarize>(.*?)</memory_summarize>', action_str, re.DOTALL
        )
        return self.query is not None

    def parse(self, action_str: str) -> Action:
        assert (
            self.query is not None
        ), 'self.query should not be None when parse is called'

        # <memory_summarize>query</memory_summarize>
        thought = action_str.replace(self.query.group(0), '').strip()
        return AgentSummarizeAction(query=self.query.group(1).strip(), thought=thought)
