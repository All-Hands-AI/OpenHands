import re

from agenthub.light_codeact_agent.prompt import (
    COMMAND_DOCS,
    EXAMPLES,
    GITHUB_MESSAGE,
    INVALID_INPUT_MESSAGE,
    SYSTEM_PREFIX,
    SYSTEM_SUFFIX,
)
from opendevin.controller.agent import Agent
from opendevin.controller.state.state import State
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
    AgentSkillsRequirement,
    JupyterRequirement,
    PluginRequirement,
)

ENABLE_GITHUB = False


def parse_response(response) -> str:
    action = response.choices[0].message.content
    for lang in ['bash', 'ipython']:
        if f'<execute_{lang}>' in action and f'</execute_{lang}>' not in action:
            action += f'</execute_{lang}>'
    return action


def action_to_str(action: Action) -> str:
    if isinstance(action, CmdRunAction):
        return f'{action.thought}\n<execute_bash>\n{action.command}\n</execute_bash>'
    elif isinstance(action, IPythonRunCellAction):
        return f'{action.thought}\n<execute_ipython>\n{action.code}\n</execute_ipython>'
    elif isinstance(action, MessageAction):
        return action.content
    return ''


def get_action_message(action: Action) -> dict[str, str] | None:
    if (
        isinstance(action, CmdRunAction)
        or isinstance(action, IPythonRunCellAction)
        or isinstance(action, MessageAction)
    ):
        return {
            'role': 'user' if action.source == 'user' else 'assistant',
            'content': action_to_str(action),
        }
    return None


def get_observation_message(obs) -> dict[str, str] | None:
    if isinstance(obs, CmdOutputObservation):
        content = 'OBSERVATION:\n' + truncate_observation(obs.content)
        content += (
            f'\n[Command {obs.command_id} finished with exit code {obs.exit_code}]]'
        )
        return {'role': 'user', 'content': content}
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
        return {'role': 'user', 'content': content}
    return None


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


class LightCodeActAgent(Agent):
    VERSION = '1.0'
    """
    LightCodeActAgent is designed for use with less capable models and for local deployment with local LLMs. It focuses on core functionalities to ensure simpler and effective performance.

    ### Overview

    Based on the LightCodeActAgentAgent, LightCodeActAgent consolidates LLM agents' actions into a unified code action space for simplicity and performance.

    At each turn, the agent can:

    1. **Converse**: Communicate with humans in natural language for clarification, confirmation, etc.
    2. **LightCodeAct**: Perform tasks by executing code
        - Execute any valid Linux `bash` command
        - Execute any valid `Python` code with an interactive Python interpreter, simulated through bash commands.

    ### Plugin System

    LightCodeActAgent leverages OpenDevin's plugin system to enhance its capabilities with access to bash action space:
    - Jupyter plugin: for IPython execution via bash commands
    - SWE-agent tool plugin: Powerful bash command line tools for software development tasks introduced by swe-agent.
    """

    sandbox_plugins: list[PluginRequirement] = [
        # NOTE: AgentSkillsRequirement must precede JupyterRequirement.
        AgentSkillsRequirement(),
        JupyterRequirement(),
    ]
    jupyter_kernel_init_code: str = 'from agentskills import *'

    system_message: str = (
        f'{SYSTEM_PREFIX}\n{GITHUB_MESSAGE}\n\n{COMMAND_DOCS}\n\n{SYSTEM_SUFFIX}'
        if ENABLE_GITHUB
        else f'{SYSTEM_PREFIX}\n\n{COMMAND_DOCS}\n\n{SYSTEM_SUFFIX}'
    )

    def __init__(
        self,
        llm: LLM,
    ) -> None:
        """
        Initializes a new instance of the LightCodeActAgent class.

        Parameters:
        - llm (LLM): The llm to be used by this agent
        """
        super().__init__(llm)
        self.reset()

    def reset(self) -> None:
        """
        Resets the LightCodeActAgent.
        """
        super().reset()

    def step(self, state: State) -> Action:
        """
        Performs one step using the LightCodeActAgent.
        This includes gathering info on previous steps and prompting the model to make a command to execute.

        Parameters:
        - state (State): used to get updated info and background commands

        Returns:
        - CmdRunAction(command) - bash command to run
        - IPythonRunCellAction(code) - IPython code to run
        - MessageAction(content) - Message action to run (e.g. ask for clarification)
        - AgentFinishAction() - end the interaction
        """
        messages: list[dict[str, str]] = [
            {'role': 'system', 'content': self.system_message},
            {
                'role': 'user',
                'content': f"Here is an example of how you can interact with the environment for task solving:\n{EXAMPLES}\n\nNOW, LET'S START!",
            },
        ]

        for prev_action, obs in state.history:
            action_message = get_action_message(prev_action)
            if action_message:
                messages.append(action_message)

            obs_message = get_observation_message(obs)
            if obs_message:
                messages.append(obs_message)

        latest_user_message = [m for m in messages if m['role'] == 'user'][-1]
        if latest_user_message:
            if latest_user_message['content'].strip() == '/exit':
                return AgentFinishAction()
            latest_user_message['content'] += (
                f'\n\nENVIRONMENT REMINDER: You have {state.max_iterations - state.iteration} turns left to complete the task.'
            )

        response = self.llm.do_completion(
            messages=messages,
            stop=[
                '</execute_ipython>',
                '</execute_bash>',
            ],
            temperature=0.0,
        )

        action_str: str = parse_response(response)
        state.num_of_chars += sum(
            len(message['content']) for message in messages
        ) + len(action_str)

        if finish_command := re.search(r'<finish>.*</finish>', action_str, re.DOTALL):
            thought = action_str.replace(finish_command.group(0), '').strip()
            return AgentFinishAction(thought=thought)
        if bash_command := re.search(
            r'<execute_bash>(.*?)</execute_bash>', action_str, re.DOTALL
        ):
            # remove the command from the action string to get thought
            thought = action_str.replace(bash_command.group(0), '').strip()
            # a command was found
            command_group = bash_command.group(1).strip()

            if command_group.strip() == 'exit':
                return AgentFinishAction()
            return CmdRunAction(command=command_group, thought=thought)
        elif python_code := re.search(
            r'<execute_ipython>(.*?)</execute_ipython>', action_str, re.DOTALL
        ):
            # a code block was found
            code_group = python_code.group(1).strip()
            thought = action_str.replace(python_code.group(0), '').strip()
            return IPythonRunCellAction(
                code=code_group,
                thought=thought,
                kernel_init_code=self.jupyter_kernel_init_code,
            )
        else:
            # Check if the action_str is a valid message action
            if action_str.strip():
                return MessageAction(content=action_str, wait_for_response=True)
            else:
                # If the action_str is empty or invalid, return the INVALID_INPUT_MESSAGE
                return MessageAction(
                    content=INVALID_INPUT_MESSAGE, wait_for_response=False
                )

    def search_memory(self, query: str) -> list[str]:
        raise NotImplementedError('Implement this abstract method')
