from openhands.agenthub.codeact_swe_agent.action_parser import (
    CodeActSWEActionParserCmdRun,
    CodeActSWEActionParserFinish,
    CodeActSWEActionParserIPythonRunCell,
    CodeActSWEActionParserMessage,
)
from openhands.controller.action_parser import ResponseParser
from openhands.events.action import Action


class CodeActSWEResponseParser(ResponseParser):
    """Parser action:
    - CmdRunAction(command) - bash command to run
    - IPythonRunCellAction(code) - IPython code to run
    - MessageAction(content) - Message action to run (e.g. ask for clarification)
    - AgentFinishAction() - end the interaction
    """

    def __init__(self):
        # Need pay attention to the item order in self.action_parsers
        super().__init__()
        self.action_parsers = [
            CodeActSWEActionParserFinish(),
            CodeActSWEActionParserCmdRun(),
            CodeActSWEActionParserIPythonRunCell(),
        ]
        self.default_parser = CodeActSWEActionParserMessage()

    def parse(self, response: str) -> Action:
        action_str = self.parse_response(response)
        return self.parse_action(action_str)

    def parse_response(self, response) -> str:
        action = response.choices[0].message.content
        if action is None:
            return ''
        for lang in ['bash', 'ipython']:
            if f'<execute_{lang}>' in action and f'</execute_{lang}>' not in action:
                action += f'</execute_{lang}>'
        return action

    def parse_action(self, action_str: str) -> Action:
        for action_parser in self.action_parsers:
            if action_parser.check_condition(action_str):
                return action_parser.parse(action_str)
        return self.default_parser.parse(action_str)
