#######

from litellm.exceptions import ContextWindowExceededError

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
from opendevin.core.exceptions import (
    ContextWindowLimitExceededError,
    SummarizeError,
    TokenLimitExceededError,
)
from opendevin.events.action import (
    Action,
    AgentDelegateAction,
    AgentFinishAction,
    AgentSummarizeAction,
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
from opendevin.memory.condenser import MemoryCondenser
from opendevin.memory.history import ShortTermHistory
from opendevin.runtime.plugins import (
    AgentSkillsRequirement,
    JupyterRequirement,
    PluginRequirement,
)
from opendevin.runtime.tools import RuntimeTool

#######

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
    elif isinstance(action, AgentSummarizeAction):
        return action.summarized_actions
    return ''


def get_action_message(action: Action) -> dict[str, str] | None:
    if (
        isinstance(action, AgentDelegateAction)
        or isinstance(action, CmdRunAction)
        or isinstance(action, IPythonRunCellAction)
        or isinstance(action, MessageAction)
        or isinstance(action, AgentSummarizeAction)
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
    elif isinstance(obs, AgentSummarizeAction):
        return {'role': 'user', 'content': obs.summarized_observations}
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
        """
        Initializes a new instance of the CodeActAgent class.

        Parameters:
        - llm (LLM): The llm to be used by this agent
        """
        super().__init__(llm)
        self.memory_condenser = MemoryCondenser(llm)
        self.attempts_to_condense = 2
        self.reset()

    def reset(self) -> None:
        """
        Resets the CodeAct Agent.
        """
        super().reset()

    def step(self, state: State) -> Action:
        """
        Performs one step using the CodeAct Agent.
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
        print('No of tokens, ' + str(self.llm.get_token_count(messages)) + '\n')
        response = None
        # give it multiple chances to get a response
        # if it fails, we'll try to condense memory
        attempt = 0
        while not response and attempt < self.attempts_to_condense:
            try:
                if self.llm.is_over_token_limit(messages):
                    raise TokenLimitExceededError()
                response = self.llm.completion(
                    messages=messages,
                    stop=[
                        '</execute_ipython>',
                        '</execute_bash>',
                        '</execute_browse>',
                    ],
                    temperature=0.0,
                )
            except (ContextWindowExceededError, TokenLimitExceededError):
                # Handle the specific exception
                print('An error occurred: ')
                attempt += 1
                # If we got a context alert, try trimming the messages length, then try again
                if self.llm.is_over_token_limit(messages):
                    # A separate call to run a summarizer
                    self.condense(state=state)
                    messages = self._get_messages(state=state)
                    # Try step again
                else:
                    print('step() failed with an unrecognized exception:')
                    raise ContextWindowLimitExceededError()

            # TODO: Manage the response for exception.
        return self.action_parser.parse(response)

    def condense(
        self,
        state: State,
    ):
        # Start past the system message, and example messages.,
        # and collect messages for summarization until we reach the desired truncation token fraction (eg 50%)
        # Do not allow truncation  for in-context examples of function calling
        history: ShortTermHistory = state.history
        messages = self._get_messages(state=state)
        token_counts = [self.llm.get_token_count([message]) for message in messages]
        message_buffer_token_count = sum(
            token_counts[2:]
        )  # no system and example message
        MESSAGE_SUMMARY_TRUNC_TOKEN_FRAC = 0.75
        desired_token_count_to_summarize = int(
            message_buffer_token_count * MESSAGE_SUMMARY_TRUNC_TOKEN_FRAC
        )

        candidate_messages_to_summarize = []
        last_summarized_event_id = history.last_summarized_event_id
        tokens_so_far = 0
        for event in history.get_events():
            if isinstance(event, AgentSummarizeAction):
                action_message = get_action_message(event)
                if action_message:
                    candidate_messages_to_summarize.append(action_message)
                    tokens_so_far += self.llm.get_token_count([action_message])
                observation_message = get_observation_message(event)
                if observation_message:
                    candidate_messages_to_summarize.append(observation_message)
                    tokens_so_far += self.llm.get_token_count([observation_message])
                continue
            else:
                message = (
                    get_action_message(event)
                    if isinstance(event, Action)
                    else get_observation_message(event)
                )
                if message:
                    candidate_messages_to_summarize.append(message)
                    tokens_so_far += self.llm.get_token_count([message])
            if tokens_so_far > desired_token_count_to_summarize:
                last_summarized_event_id = event.id
                break

        # TODO: Add functionality for preserving last N messages
        # MESSAGE_SUMMARY_TRUNC_KEEP_N_LAST = 3
        # if preserve_last_N_messages:
        #     candidate_messages_to_summarize = candidate_messages_to_summarize[:-MESSAGE_SUMMARY_TRUNC_KEEP_N_LAST]
        #     token_counts = token_counts[:-MESSAGE_SUMMARY_TRUNC_KEEP_N_LAST]

        print(f'MESSAGE_SUMMARY_TRUNC_TOKEN_FRAC={MESSAGE_SUMMARY_TRUNC_TOKEN_FRAC}')
        # print(f'MESSAGE_SUMMARY_TRUNC_KEEP_N_LAST={MESSAGE_SUMMARY_TRUNC_KEEP_N_LAST}')
        print(f'token_counts={token_counts}')
        print(f'message_buffer_token_count={message_buffer_token_count}')
        print(f'desired_token_count_to_summarize={desired_token_count_to_summarize}')
        print(
            f'len(candidate_messages_to_summarize)={len(candidate_messages_to_summarize)}'
        )

        if len(candidate_messages_to_summarize) == 0:
            raise SummarizeError(
                f"Summarize error: tried to run summarize, but couldn't find enough messages to compress [len={len(messages)}]"
            )

        # TODO: Try to make an assistant message come after the cutoff

        message_sequence_to_summarize = candidate_messages_to_summarize

        if len(message_sequence_to_summarize) <= 1:
            # This prevents a potential infinite loop of summarizing the same message over and over
            raise SummarizeError(
                f"Summarize error: tried to run summarize, but couldn't find enough messages to compress [len={len(message_sequence_to_summarize)} <= 1]"
            )
        else:
            print(
                f'Attempting to summarize with last summarized event id = {last_summarized_event_id}'
            )

        summary_action = self.memory_condenser.summarize_messages(
            message_sequence_to_summarize=message_sequence_to_summarize
        )
        summary_action.last_summarized_event_id = last_summarized_event_id
        print(f'Got summary: {summary_action}')
        history.add_summary(summary_action)
        print('Added summary to history')

    def search_memory(self, query: str) -> list[str]:
        raise NotImplementedError('Implement this abstract method')

    def _get_messages(self, state: State) -> list[dict[str, str]]:
        messages = [
            {'role': 'system', 'content': self.system_message},
            {'role': 'user', 'content': self.in_context_example},
        ]

        for event in state.history.get_events():
            if isinstance(event, AgentSummarizeAction):
                action_message = get_action_message(event)
                print('Got Summary Message')
                if action_message:
                    messages.append(action_message)
                observation_message = get_observation_message(event)
                if observation_message:
                    messages.append(observation_message)
                continue

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
