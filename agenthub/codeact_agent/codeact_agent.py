import re
from typing import List, Mapping

from opendevin.action import (
    Action,
    AgentEchoAction,
    AgentFinishAction,
    AgentTalkAction,
    NullAction,
    IPythonRunCellAction,
    CmdRunAction,
)
from opendevin.agent import Agent
from opendevin.llm.llm import LLM
from opendevin.observation import (
    UserMessageObservation,
    AgentMessageObservation,
    CmdOutputObservation,
    IPythonRunCellObservation
)
from opendevin.state import State
from opendevin.sandbox.plugins import PluginRequirement, JupyterRequirement, SWEAgentCommandsRequirement
from agenthub.codeact_agent.prompt import SYSTEM_MESSAGE, EXAMPLES


def parse_response(response) -> str:
    action = response.choices[0].message.content
    for lang in ['bash', 'ipython']:
        if f'<execute_{lang}>' in action and f'</execute_{lang}>' not in action:
            action += f'</execute_{lang}>'
    return action


class CodeActAgent(Agent):
    """
    The Code Act Agent is a minimalist agent.
    The agent works by passing the model a list of action-observation pairs and prompting the model to take the next step.
    """

    sandbox_plugins: List[PluginRequirement] = [JupyterRequirement(), SWEAgentCommandsRequirement()]
    SUPPORTED_ACTIONS = (
        CmdRunAction,
        IPythonRunCellAction,
        AgentEchoAction,
        AgentTalkAction,
        NullAction
    )
    SUPPORTED_OBSERVATIONS = (
        AgentMessageObservation,
        UserMessageObservation,
        CmdOutputObservation,
        IPythonRunCellObservation
    )

    def __init__(
        self,
        llm: LLM,
    ) -> None:
        """
        Initializes a new instance of the CodeActAgent class.

        Parameters:
        - llm (LLM): The llm to be used by this agent
        """
        super().__init__(llm)
        self.messages: List[Mapping[str, str]] = []

    def step(self, state: State) -> Action:
        """
        Performs one step using the Code Act Agent.
        This includes gathering info on previous steps and prompting the model to make a command to execute.

        Parameters:
        - state (State): used to get updated info and background commands

        Returns:
        - CmdRunAction(command) - command action to run
        - AgentEchoAction(content=INVALID_INPUT_MESSAGE) - invalid command output

        Raises:
        - NotImplementedError - for actions other than CmdOutputObservation or AgentMessageObservation
        """

        if len(self.messages) == 0:
            assert state.plan.main_goal, 'Expecting instruction to be set'
            self.messages = [
                {'role': 'system', 'content': SYSTEM_MESSAGE},
                {
                    'role': 'user',
                    'content': (
                        f'Here is an example of how you can interact with the environment for task solving:\n{EXAMPLES}\n\n'
                        f"NOW, LET'S START!\n\n{state.plan.main_goal}"
                    )
                },
            ]
        updated_info = state.updated_info
        if updated_info:
            for prev_action, obs in updated_info:
                assert isinstance(
                    prev_action, self.SUPPORTED_ACTIONS
                ), f'{prev_action.__class__} is not supported (supported: {self.SUPPORTED_ACTIONS})'
                # prev_action is already added to self.messages when returned

                # handle observations
                assert isinstance(
                    obs, self.SUPPORTED_OBSERVATIONS
                ), f'{obs.__class__} is not supported (supported: {self.SUPPORTED_OBSERVATIONS})'
                if isinstance(obs, (AgentMessageObservation, UserMessageObservation)):
                    self.messages.append(
                        {'role': 'user', 'content': obs.content})
                elif isinstance(obs, CmdOutputObservation):
                    content = 'OBSERVATION:\n' + obs.content
                    content += f'\n[Command {obs.command_id} finished with exit code {obs.exit_code}]]'
                    self.messages.append({'role': 'user', 'content': content})
                elif isinstance(obs, IPythonRunCellObservation):
                    content = 'OBSERVATION:\n' + obs.content
                    self.messages.append({'role': 'user', 'content': content})
                else:
                    raise NotImplementedError(
                        f'Unknown observation type: {obs.__class__}'
                    )

        response = self.llm.completion(
            messages=self.messages,
            stop=[
                '</execute_ipython>',
                '</execute_bash>',
                # chatML in case ollama does not stop
                '<|im_end|>',
                '<|im_start|>'
            ],
            temperature=0.0
        )
        action_str: str = parse_response(response)
        state.num_of_chars += sum(
            len(message['content']) for message in self.messages
        ) + len(action_str)
        self.messages.append({'role': 'assistant', 'content': action_str})

        bash_command = re.search(r'<execute_bash>(.*)</execute_bash>', action_str, re.DOTALL)
        python_code = re.search(r'<execute_ipython>(.*)</execute_ipython>', action_str, re.DOTALL)
        if bash_command is not None:
            # remove the command from the action string to get thought
            thought = action_str.replace(bash_command.group(0), '').strip()
            # a command was found
            command_group = bash_command.group(1).strip()
            if command_group.strip() == 'exit':
                return AgentFinishAction()
            return CmdRunAction(command=command_group, thought=thought)
        elif python_code is not None:
            # a code block was found
            code_group = python_code.group(1).strip()
            thought = action_str.replace(python_code.group(0), '').strip()
            # print(f"PYTHON CODE: '{code_group}'")
            return IPythonRunCellAction(code=code_group, thought=thought)
        else:
            # We assume the agent is GOOD enough that when it returns pure NL,
            # it want to talk to the user
            return AgentTalkAction(content=action_str)

    def search_memory(self, query: str) -> List[str]:
        raise NotImplementedError('Implement this abstract method')
