import re
from typing import List, Mapping

from agenthub.codeact_agent.prompt import EXAMPLES, SYSTEM_MESSAGE
from opendevin.controller.agent import Agent
from opendevin.controller.state.state import State
from opendevin.core.logger import opendevin_logger as logger
from opendevin.events.action import (
    Action,
    AgentEchoAction,
    AgentFinishAction,
    AgentTalkAction,
    CmdRunAction,
    IPythonRunCellAction,
    NullAction,
)
from opendevin.events.observation import (
    AgentMessageObservation,
    CmdOutputObservation,
    IPythonRunCellObservation,
    UserMessageObservation,
)
from opendevin.llm.llm import LLM, completion_cost
from opendevin.runtime.plugins import (
    JupyterRequirement,
    PluginRequirement,
    SWEAgentCommandsRequirement,
)


def parse_response(response) -> str:
    action = response.choices[0].message.content
    for lang in ['bash', 'ipython']:
        if f'<execute_{lang}>' in action and f'</execute_{lang}>' not in action:
            action += f'</execute_{lang}>'
    return action


def truncate_observation(observation: str, max_chars: int = 5000) -> str:
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
                raise ValidationError(self.error_messages['invalid'], code='invalid')s
    EOF
    """
    if 'edit' in bash_command:
        # edit\s(\d+):(\d+)([\s\S]*)end_of_edit
        # replace
        bash_command_before = bash_command
        bash_command = re.sub(
            r'edit\s(\d+):(\d+)([\s\S]*)end_of_edit',
            r'edit \1:\2 <<EOF\3EOF',
            bash_command,
        )
        logger.info(
            f'SWE-agent edit hack applied:\n- Before:\n{bash_command_before}\n- After:\n{bash_command}'
        )
    return bash_command


class CodeActAgent(Agent):
    """
    The Code Act Agent is a minimalist agent.
    The agent works by passing the model a list of action-observation pairs and prompting the model to take the next step.

    ### Overview

    This agent implements the CodeAct idea ([paper](https://arxiv.org/abs/2402.13463), [tweet](https://twitter.com/xingyaow_/status/1754556835703751087)) that consolidates LLM agents’ **act**ions into a unified **code** action space for both *simplicity* and *performance* (see paper for more details).

    The conceptual idea is illustrated below. At each turn, the agent can:

    1. **Converse**: Communicate with humans in natural language to ask for clarification, confirmation, etc.
    2. **CodeAct**: Choose to perform the task by executing code
    - Execute any valid Linux `bash` command
    - Execute any valid `Python` code with [an interactive Python interpreter](https://ipython.org/). This is simulated through `bash` command, see plugin system below for more details.

    ![image](https://github.com/OpenDevin/OpenDevin/assets/38853559/92b622e3-72ad-4a61-8f41-8c040b6d5fb3)

    ### Plugin System

    To make the CodeAct agent more powerful with only access to `bash` action space, CodeAct agent leverages OpenDevin's plugin system:
    - [Jupyter plugin](https://github.com/OpenDevin/OpenDevin/tree/main/opendevin/runtime/plugins/jupyter): for IPython execution via bash command
    - [SWE-agent tool plugin](https://github.com/OpenDevin/OpenDevin/tree/main/opendevin/runtime/plugins/swe_agent_commands): Powerful bash command line tools for software development tasks introduced by [swe-agent](https://github.com/princeton-nlp/swe-agent).

    ### Demo

    https://github.com/OpenDevin/OpenDevin/assets/38853559/f592a192-e86c-4f48-ad31-d69282d5f6ac

    *Example of CodeActAgent with `gpt-4-turbo-2024-04-09` performing a data science task (linear regression)*

    ### Work-in-progress & Next step

    [] Support web-browsing
    [] Complete the workflow for CodeAct agent to submit Github PRs

    """

    sandbox_plugins: List[PluginRequirement] = [
        JupyterRequirement(),
        SWEAgentCommandsRequirement(),
    ]
    SUPPORTED_ACTIONS = (
        CmdRunAction,
        IPythonRunCellAction,
        AgentEchoAction,
        AgentTalkAction,
        NullAction,
    )
    SUPPORTED_OBSERVATIONS = (
        AgentMessageObservation,
        UserMessageObservation,
        CmdOutputObservation,
        IPythonRunCellObservation,
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
        self.cost_accumulator = 0

    def step(self, state: State) -> Action:
        """
        Performs one step using the CodeAct Agent.
        This includes gathering info on previous steps and prompting the model to make a command to execute.

        Parameters:
        - state (State): used to get updated info and background commands

        Returns:
        - CmdRunAction(command) - bash command to run
        - IPythonRunCellAction(code) - IPython code to run
        - AgentTalkAction(content) - Talk action to run (e.g. ask for clarification)
        - AgentFinishAction() - end the interaction
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
                    ),
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
                    self.messages.append({'role': 'user', 'content': obs.content})

                    # User wants to exit
                    if obs.content.strip() == '/exit':
                        return AgentFinishAction()
                elif isinstance(obs, CmdOutputObservation):
                    content = 'OBSERVATION:\n' + truncate_observation(obs.content)
                    content += f'\n[Command {obs.command_id} finished with exit code {obs.exit_code}]]'
                    self.messages.append({'role': 'user', 'content': content})

                elif isinstance(obs, IPythonRunCellObservation):
                    content = 'OBSERVATION:\n' + obs.content
                    # replace base64 images with a placeholder
                    splited = content.split('\n')
                    for i, line in enumerate(splited):
                        if '![image](data:image/png;base64,' in line:
                            splited[i] = (
                                '![image](data:image/png;base64, ...) already displayed to user'
                            )
                    content = '\n'.join(splited)
                    content = truncate_observation(content)
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
            ],
            temperature=0.0,
        )
        cur_cost = completion_cost(completion_response=response)
        self.cost_accumulator += cur_cost
        logger.info(
            f'Cost: {cur_cost:.2f} USD | Accumulated Cost: {self.cost_accumulator:.2f} USD'
        )
        action_str: str = parse_response(response)
        state.num_of_chars += sum(
            len(message['content']) for message in self.messages
        ) + len(action_str)
        self.messages.append({'role': 'assistant', 'content': action_str})

        if bash_command := re.search(
            r'<execute_bash>(.*)</execute_bash>', action_str, re.DOTALL
        ):
            # remove the command from the action string to get thought
            thought = action_str.replace(bash_command.group(0), '').strip()
            # a command was found
            command_group = bash_command.group(1).strip()
            command_group = swe_agent_edit_hack(command_group)

            if command_group.strip() == 'exit':
                return AgentFinishAction()
            return CmdRunAction(command=command_group, thought=thought)
        elif python_code := re.search(
            r'<execute_ipython>(.*)</execute_ipython>', action_str, re.DOTALL
        ):
            # a code block was found
            code_group = python_code.group(1).strip()
            thought = action_str.replace(python_code.group(0), '').strip()
            return IPythonRunCellAction(code=code_group, thought=thought)
        else:
            # We assume the LLM is GOOD enough that when it returns pure natural language
            # it want to talk to the user
            return AgentTalkAction(content=action_str)

    def search_memory(self, query: str) -> List[str]:
        raise NotImplementedError('Implement this abstract method')
