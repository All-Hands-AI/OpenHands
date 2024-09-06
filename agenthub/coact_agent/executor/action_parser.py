from agenthub.codeact_agent.action_parser import (
    CodeActActionParserAgentDelegate,
    CodeActActionParserCmdRun,
    CodeActActionParserFinish,
    CodeActActionParserIPythonRunCell,
    CodeActActionParserMessage,
    CodeActResponseParser,
)


class ExecutorResponseParser(CodeActResponseParser):
    """Parser action:
    - CmdRunAction(command) - bash command to run
    - IPythonRunCellAction(code) - IPython code to run
    - AgentDelegateAction(agent, inputs) - delegate action for (sub)task
    - MessageAction(content) - Message action to run (e.g. ask for clarification)
    - AgentFinishAction() - end the interaction
    """

    def __init__(self):
        # Need pay attention to the item order in self.action_parsers
        super().__init__()
        self.action_parsers = [
            CodeActActionParserFinish(),
            CodeActActionParserCmdRun(),
            CodeActActionParserIPythonRunCell(),
            CodeActActionParserAgentDelegate(),
            # TODO: additional parsers
        ]
        self.default_parser = CodeActActionParserMessage()

    def parse_response(self, response) -> str:
        action = response.choices[0].message.content
        if action is None:
            return ''
        for lang in ['bash', 'ipython', 'browse']:
            if f'<execute_{lang}>' in action and f'</execute_{lang}>' not in action:
                action += f'</execute_{lang}>'
        return action
