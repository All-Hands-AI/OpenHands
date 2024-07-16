from agenthub.codeact_agent.action_parser import CodeActResponseParser
from agenthub.codeact_agent.prompt import (
    COMMAND_DOCS,
    EXAMPLES,
    GITHUB_MESSAGE,
    SYSTEM_PREFIX,
    SYSTEM_SUFFIX,
)
from opendevin.controller.agent import Agent
from opendevin.controller.state.state import State
from opendevin.core.config import config
from opendevin.events.action import (
    Action,
    AgentDelegateAction,
    AgentFinishAction,
    CmdRunAction,
    IPythonRunCellAction,
    MessageAction,
)
from opendevin.events.observation import (
    AgentDelegateObservation,
    CmdOutputObservation,
    IPythonRunCellObservation,
)
from opendevin.events.serialization.event import truncate_content
from opendevin.llm.llm import LLM
from opendevin.runtime.plugins import (
    AgentSkillsRequirement,
    JupyterRequirement,
    PluginRequirement,
)
from opendevin.runtime.tools import RuntimeTool

ENABLE_GITHUB = True


def action_to_str(action: Action) -> str:
    if isinstance(action, CmdRunAction):
        return f'{action.thought}\n<execute_bash>\n{action.command}\n</execute_bash>'
    elif isinstance(action, IPythonRunCellAction):
        return f'{action.thought}\n<execute_ipython>\n{action.code}\n</execute_ipython>'
    elif isinstance(action, AgentDelegateAction):
        return f'{action.thought}\n<execute_browse>\n{action.inputs["task"]}\n</execute_browse>'
    elif isinstance(action, MessageAction):
        return action.content
    return ''


def get_action_message(action: Action) -> dict[str, str] | None:
    if (
        isinstance(action, AgentDelegateAction)
        or isinstance(action, CmdRunAction)
        or isinstance(action, IPythonRunCellAction)
        or isinstance(action, MessageAction)
    ):
        return {
            'role': 'user' if action.source == 'user' else 'assistant',
            'content': action_to_str(action),
        }
    return None


def get_observation_message(obs) -> dict[str, str] | None:
    max_message_chars = config.get_llm_config_from_agent(
        'CodeActAgent'
    ).max_message_chars
    if isinstance(obs, CmdOutputObservation):
        content = 'OBSERVATION:\n' + truncate_content(obs.content, max_message_chars)
        content += (
            f'\n[Command {obs.command_id} finished with exit code {obs.exit_code}]'
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
        content = truncate_content(content, max_message_chars)
        return {'role': 'user', 'content': content}
    elif isinstance(obs, AgentDelegateObservation):
        content = 'OBSERVATION:\n' + truncate_content(
            str(obs.outputs), max_message_chars
        )
        return {'role': 'user', 'content': content}
    return None


# FIXME: We can tweak these two settings to create MicroAgents specialized toward different area
def get_system_message() -> str:
    if ENABLE_GITHUB:
        return f'{SYSTEM_PREFIX}\n{GITHUB_MESSAGE}\n\n{COMMAND_DOCS}\n\n{SYSTEM_SUFFIX}'
    else:
        return f'{SYSTEM_PREFIX}\n\n{COMMAND_DOCS}\n\n{SYSTEM_SUFFIX}'


def get_in_context_example() -> str:
    return EXAMPLES


class CodeActAgent(Agent):
    VERSION = '1.8'
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
        # NOTE: AgentSkillsRequirement need to go before JupyterRequirement, since
        # AgentSkillsRequirement provides a lot of Python functions,
        # and it needs to be initialized before Jupyter for Jupyter to use those functions.
        AgentSkillsRequirement(),
        JupyterRequirement(),
    ]
    runtime_tools: list[RuntimeTool] = [RuntimeTool.BROWSER]

    system_message: str = get_system_message()
    in_context_example: str = f"Here is an example of how you can interact with the environment for task solving:\n{get_in_context_example()}\n\nNOW, LET'S START!"

    action_parser = CodeActResponseParser()

    def __init__(
        self,
        llm: LLM,
    ) -> None:
        """Initializes a new instance of the CodeActAgent class.

        Parameters:
        - llm (LLM): The llm to be used by this agent
        """
        super().__init__(llm)
        self.reset()

    def reset(self) -> None:
        """Resets the CodeAct Agent."""
        super().reset()

    def step(self, state: State) -> Action:
        """Performs one step using the CodeAct Agent.
        This includes gathering info on previous steps and prompting the model to make a command to execute.

        Parameters:
        - state (State): used to get updated info

        Returns:
        - CmdRunAction(command) - bash command to run
        - IPythonRunCellAction(code) - IPython code to run
        - AgentDelegateAction(agent, inputs) - delegate action for (sub)task
        - MessageAction(content) - Message action to run (e.g. ask for clarification)
        - AgentFinishAction() - end the interaction
        """
        # if we're done, go back
        latest_user_message = state.history.get_last_user_message()
        if latest_user_message and latest_user_message.strip() == '/exit':
            return AgentFinishAction()

        # prepare what we want to send to the LLM
        messages: list[dict[str, str]] = self._get_messages(state)

        response = self.llm.completion(
            messages=messages,
            stop=[
                '</execute_ipython>',
                '</execute_bash>',
                '</execute_browse>',
            ],
            temperature=0.0,
        )
        return self.action_parser.parse(response)

    def _get_messages(self, state: State) -> list[dict[str, str]]:
        messages = [
            {'role': 'system', 'content': self.system_message},
            {'role': 'user', 'content': self.in_context_example},
        ]

        for event in state.history.get_events():
            # create a regular message from an event
            message = (
                get_action_message(event)
                if isinstance(event, Action)
                else get_observation_message(event)
            )

            # add regular message
            if message:
                messages.append(message)

        # the latest user message is important:
        # we want to remind the agent of the environment constraints
        latest_user_message = next(
            (m for m in reversed(messages) if m['role'] == 'user'), None
        )

        # add a reminder to the prompt
        if latest_user_message:
            latest_user_message['content'] += (
                f'\n\nENVIRONMENT REMINDER: You have {state.max_iterations - state.iteration} turns left to complete the task. When finished reply with <finish></finish>'
            )

        return messages
