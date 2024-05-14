import re

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
)
from opendevin.events.observation import (
    CmdOutputObservation,
    IPythonRunCellObservation,
)
from opendevin.llm.llm import LLM
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

    sandbox_plugins: list[PluginRequirement] = [
        JupyterRequirement(),
        SWEAgentCommandsRequirement(),
    ]

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
        self.reset()

    def reset(self) -> None:
        """
        Resets the CodeAct Agent.
        """
        super().reset()
        self.messages: list[dict[str, str]] = [
            {'role': 'system', 'content': SYSTEM_MESSAGE},
            {
                'role': 'user',
                'content': f"Here is an example of how you can interact with the environment for task solving:\n{EXAMPLES}\n\nNOW, LET'S START!",
            },
        ]
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
        - MessageAction(content) - Message action to run (e.g. ask for clarification)
        - AgentFinishAction() - end the interaction
        """

        updated_info = state.updated_info
        if updated_info:
            for prev_action, obs in updated_info:
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

        latest_user_message = [m for m in self.messages if m['role'] == 'user'][-1]
        if latest_user_message:
            latest_user_message['content'] += (
                f'\n\nENVIRONMENT REMINDER: You have {state.max_iterations - state.iteration - 1} turns left to complete the task.'
            )

        response = self.llm.completion(
            messages=self.messages,
            stop=[
                '</execute_ipython>',
                '</execute_bash>',
            ],
            temperature=0.0,
        )

        self.log_cost(response)

        action_str: str = parse_response(response)
        state.num_of_chars += sum(
            len(message['content']) for message in self.messages
        ) + len(action_str)
        self.messages.append({'role': 'assistant', 'content': action_str})

        if finish_command := re.search(r'<finish>.*</finish>', action_str, re.DOTALL):
            thought = action_str.replace(finish_command.group(0), '').strip()
            return AgentFinishAction(thought=thought)
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
