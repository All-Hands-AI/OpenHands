import re
from typing import List, Mapping

from opendevin.action import (
    Action,
    AgentEchoAction,
    AgentFinishAction,
    AgentTalkAction,
    IPythonRunCellAction,
    CmdRunAction,
)
from opendevin.agent import Agent
from opendevin.llm.llm import LLM
from opendevin.observation import (
    UserMessageObservation,
    AgentMessageObservation,
    CmdOutputObservation,
)
from opendevin.parse_commands import parse_command_file
from opendevin.state import State
from opendevin.sandbox.plugins import PluginRequirement, JupyterRequirement

COMMAND_DOCS = parse_command_file()
COMMAND_SEGMENT = (
    f"""

Apart from the standard bash commands, you can also use the following special commands:
{COMMAND_DOCS}
"""
    if COMMAND_DOCS is not None
    else ''
)
# SYSTEM_MESSAGE = f"""A multi-turn interaction between a curious user and an artificial intelligence assistant.
# The assistant gives helpful, detailed, and polite answers to the user's questions.

# ## Python Interaction
# The assistant can interact with an interactive Python (Jupyter Notebook) environment and receive the corresponding output when needed. The code should be enclosed using "<execute_ipython>" tag, for example: <execute_ipython> print("Hello World!") </execute_ipython>.

# ## Bash Commands
# The assistant can execute bash commands on behalf of the user by wrapping them with <execute_bash> and </execute_bash>. For example, you can list the files in the current directory by <execute_bash> ls </execute_bash>.

# ## General Guidelines
# The assistant should attempt fewer things at a time instead of putting too much code in one <execute> block.
# The assistant should stop "execute" and provide an answer when they have already obtained the answer from the execution result. Whenever possible, execute the command or code for the user using <execute_bash> or <execute_ipython> instead of providing it as a response.
# The assistant's response should be concise, but do express their thoughts."""

SYSTEM_MESSAGE = """A chat between a curious user and an artificial intelligence assistant. The assistant gives helpful, detailed, and polite answers to the user's questions.
The assistant can interact with an interactive Python (Jupyter Notebook) environment and receive the corresponding output when needed. The code should be enclosed using "<execute_ipython>" tag, for example: <execute_ipython> print("Hello World!") </execute_ipython>.
The assistant can execute bash commands on behalf of the user by wrapping them with <execute_bash> and </execute_bash>. For example, you can list the files in the current directory by <execute_bash> ls </execute_bash>.
The assistant should attempt fewer things at a time instead of putting too much commands OR code in one "execute" block.
The assistant can install Python packages through bash by <execute_bash> pip install [package needed] </execute_bash> and should always import packages and define variables before starting to use them.
The assistant should stop <execute> and provide an answer when they have already obtained the answer from the execution result. Whenever possible, execute the code for the user using <execute_ipython> or <execute_bash> instead of providing it.
The assistant's response should be concise, but do express their thoughts.
When you are done with your task, you can <execute_bash> exit </execute_bash> to complete the task.
"""

INVALID_INPUT_MESSAGE = (
    "I don't understand your input. \n"
    'If you want to execute a bash command, please use <execute_bash> YOUR_COMMAND_HERE </execute_bash>.\n'
    'If you want to execute a block of Python code, please use <execute_ipython> YOUR_COMMAND_HERE </execute_ipython>.\n'
)


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

    sandbox_plugins: List[PluginRequirement] = [JupyterRequirement()]
    SUPPORTED_ACTIONS = (
        CmdRunAction,
        IPythonRunCellAction,
        AgentEchoAction,
        AgentTalkAction,
    )
    SUPPORTED_OBSERVATIONS = (
        AgentMessageObservation,
        UserMessageObservation,
        CmdOutputObservation
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
                {'role': 'user', 'content': state.plan.main_goal},
            ]
        updated_info = state.updated_info
        if updated_info:
            for prev_action, obs in updated_info:
                # print("PREV ACTION: ", prev_action.__class__, prev_action)
                # print("PREV OBS: ", obs.__class__, obs)
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
                else:
                    raise NotImplementedError(
                        f'Unknown observation type: {obs.__class__}'
                    )

        # print("-----------------")
        # for msg in self.messages:
        #     role = msg['role']
        #     content = msg['content']
        #     print(f"{role.upper()}:\n{content}")
        #     print('---')
        # print("-----------------")
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
        # print("ACTION STR: ", action_str)
        self.messages.append({'role': 'assistant', 'content': action_str})

        bash_command = re.search(r'<execute_bash>(.*)</execute_bash>', action_str, re.DOTALL)
        python_code = re.search(r'<execute_ipython>(.*)</execute_ipython>', action_str, re.DOTALL)
        if bash_command is not None:
            # a command was found
            command_group = bash_command.group(1)
            # print("BASH COMMAND: ", command_group)
            if command_group.strip() == 'exit':
                return AgentFinishAction()
            return CmdRunAction(command=command_group)
        elif python_code is not None:
            # a code block was found
            code_group = python_code.group(1)
            # print("PYTHON CODE: ", code_group)
            return IPythonRunCellAction(code=code_group.strip())
        else:
            # return AgentEchoAction(
            #     content=INVALID_INPUT_MESSAGE
            # )  # warning message to itself

            # We assume the agent is GOOD enough that when it returns pure NL,
            # it want to talk to the user
            return AgentTalkAction(content=action_str)

    def search_memory(self, query: str) -> List[str]:
        raise NotImplementedError('Implement this abstract method')
