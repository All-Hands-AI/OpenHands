import re
from typing import Mapping

from agenthub.codeact_agent.prompt import EXAMPLES, SYSTEM_MESSAGE
from opendevin.controller.agent import Agent
from opendevin.controller.state.state import State
from opendevin.core.logger import opendevin_logger as logger
from opendevin.events.action import (
    Action,
    AgentFinishAction,
    CmdRunAction,
    IPythonRunCellAction,
    MessageAction,
    NullAction,
)
from opendevin.events.observation import (
    CmdOutputObservation,
    IPythonRunCellObservation,
    NullObservation,
)
from opendevin.sandbox.plugins import JupyterRequirement, PluginRequirement
from opendevin.state import State

SYSTEM_MESSAGE = """You are a helpful assistant. You will be provided access (as root) to a bash shell to complete user-provided tasks.
You will be able to execute commands in the bash shell, interact with the file system, install packages, and receive the output of your commands.

DO NOT provide code in ```triple backticks```. Instead, you should execute bash command on behalf of the user by wrapping them with <execute> and </execute>.
For example:

You can list the files in the current directory by executing the following command:
<execute>ls</execute>

You can also install packages using pip:
<execute> pip install numpy </execute>

You can also write a block of code to a file:
<execute>
echo "import math
print(math.pi)" > math.py
</execute>

When you are done, execute the following to close the shell and end the conversation:
<execute>exit</execute>
"""

INVALID_INPUT_MESSAGE = (
    "I don't understand your input. \n"
    'If you want to execute command, please use <execute> YOUR_COMMAND_HERE </execute>.\n'
    'If you already completed the task, please exit the shell by generating: <execute> exit </execute>.'
)


def parse_response(response) -> str:
    action = response.choices[0].message.content
    if '<execute>' in action and '</execute>' not in action:
        action += '</execute>'
    return action


def truncate_observation(observation: str, max_chars: int = 10_000) -> str:
    """
    Truncate the middle of the observation if it is too long.
    """
    if len(observation) <= max_chars:
        return observation
    half = max_chars // 2
    return (
        observation[:half]
        + '\n[... Observation truncated due to length ...]\n'
        + observation[-half:]
    )


def swe_agent_edit_hack(bash_command: str) -> str:
    """
    Hack to handle the SWE-agent edit command. The vanilla edit command will hang the SSHBox.

    REPLACE THIS:
    edit 683:693
            try:
                return list(urlsplit(url))
            except ValueError:
                raise ValidationError(self.error_messages['invalid'], code='invalid')
    end_of_edit

    WITH THIS:
    edit 683:693 <<EOF
            try:
                return list(urlsplit(url))
            except ValueError:
                raise ValidationError(self.error_messages['invalid'], code='invalid')
    EOF
    """
    if 'edit' in bash_command:
        # edit\s(\d+):(\d+)([\s\S]*)end_of_edit
        # replace
        bash_command = re.sub(
            r'edit\s(\d+):(\d+)([\s\S]*?)end_of_edit',
            r'edit \1:\2 <<EOF\3EOF',
            bash_command,
        )
    return bash_command


class CodeActAgent(Agent):
    VERSION = '1.1'
    """
    The Code Act Agent is a minimalist agent.
    The agent works by passing the model a list of action-observation pairs and prompting the model to take the next step.
    """

    sandbox_plugins: list[PluginRequirement] = [
        JupyterRequirement(),
        SWEAgentCommandsRequirement(),
    ]
    SUPPORTED_ACTIONS = (
        CmdRunAction,
        IPythonRunCellAction,
        MessageAction,
        NullAction,
    )
    SUPPORTED_OBSERVATIONS = (
        CmdOutputObservation,
        IPythonRunCellObservation,
        NullObservation,
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
        self.messages: list[Mapping[str, str]] = []
        self.cost_accumulator = 0

    def step(self, state: State) -> Action:
        """
        Performs one step using the Code Act Agent.
        This includes gathering info on previous steps and prompting the model to make a command to execute.

        Parameters:
        - state (State): used to get updated info and background commands

        Returns:
        - CmdRunAction(command) - bash command to run
        - IPythonRunCellAction(code) - IPython code to run
        - MessageAction(content) - Message action to run (e.g. ask for clarification)
        - AgentFinishAction() - end the interaction
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
                assert isinstance(
                    prev_action, self.SUPPORTED_ACTIONS
                ), f'{prev_action.__class__} is not supported (supported: {self.SUPPORTED_ACTIONS})'
                if (
                    isinstance(prev_action, MessageAction)
                    and prev_action.source == 'user'
                ):
                    self.messages.append(
                        {'role': 'user', 'content': prev_action.content}
                    )
                    if prev_action.content.strip() == '/exit':
                        # User wants to exit
                        return AgentFinishAction()

                # handle observations
                assert isinstance(
                    obs, self.SUPPORTED_OBSERVATIONS
                ), f'{obs.__class__} is not supported (supported: {self.SUPPORTED_OBSERVATIONS})'

                if isinstance(obs, CmdOutputObservation):
                    content = 'OBSERVATION:\n' + truncate_observation(obs.content)
                    content += f'\n[Command {obs.command_id} finished with exit code {obs.exit_code}]]'
                    self.messages.append({'role': 'user', 'content': content})

                elif isinstance(obs, IPythonRunCellObservation):
                    content = 'OBSERVATION:\n' + obs.content
                    # replace base64 images with a placeholder
                    splitted = content.split('\n')
                    for i, line in enumerate(splitted):
                        if '![image](data:image/png;base64,' in line:
                            splitted[i] = (
                                '![image](data:image/png;base64, ...) already displayed to user'
                            )
                    content = '\n'.join(splitted)
                    content = truncate_observation(content)
                    self.messages.append({'role': 'user', 'content': content})
                elif isinstance(obs, NullObservation):
                    pass
                else:
                    raise NotImplementedError(
                        f'Unknown observation type: {obs.__class__}'
                    )
        response = self.llm.completion(
            messages=self.messages,
            stop=['</execute>'],
            temperature=0.0
        )

        self.log_cost(response)

        action_str: str = parse_response(response)
        state.num_of_chars += sum(len(message['content'])
                                  for message in self.messages) + len(action_str)
        self.messages.append({'role': 'assistant', 'content': action_str})

        command = re.search(r'<execute>(.*)</execute>', action_str, re.DOTALL)
        if command is not None:
            # a command was found
            command_group = bash_command.group(1).strip()
            command_group = swe_agent_edit_hack(command_group)

            if command_group.strip() == 'exit':
                return AgentFinishAction()
            return CmdRunAction(command=command_group)
            # # execute the code
            # # TODO: does exit_code get loaded into Message?
            # exit_code, observation = self.env.execute(command_group)
            # self._history.append(Message(Role.ASSISTANT, observation))
        else:
            # We assume the LLM is GOOD enough that when it returns pure natural language
            # it want to talk to the user
            return MessageAction(content=action_str, wait_for_response=True)

    def search_memory(self, query: str) -> list[str]:
        raise NotImplementedError('Implement this abstract method')

    def log_cost(self, response):
        cur_cost = self.llm.completion_cost(response)
        self.cost_accumulator += cur_cost
        logger.info(
            'Cost: %.2f USD | Accumulated Cost: %.2f USD',
            cur_cost,
            self.cost_accumulator,
        )
